/**
 * payments-paddle.js — Paddle billing integration for ilmariai.com
 *
 * Handles:
 *  - Webhook events (subscription created / updated / canceled)
 *  - Checkout session creation (client-side Paddle.js handles the overlay)
 *  - Subscription management (cancel, get info)
 *
 * Setup in appify server.js:
 *   const paddleRouter = require('./routes/payments-paddle');
 *   app.use('/api/paddle', express.raw({ type: 'application/json' }), paddleRouter);  // webhook needs raw body
 *   app.use('/api/paddle', paddleRouter);
 *
 * Required env vars:
 *   PADDLE_API_KEY          — Paddle API secret key (sandbox or production)
 *   PADDLE_WEBHOOK_SECRET   — from Paddle dashboard → Notifications
 *   PADDLE_ENV              — "sandbox" or "production" (default: sandbox)
 *
 *   Price IDs (from Paddle dashboard):
 *   PADDLE_PRICE_MARKETING_BASIC
 *   PADDLE_PRICE_MARKETING_PRO
 *   PADDLE_PRICE_MARKETING_BUSINESS
 *   PADDLE_PRICE_BUNDLE_STARTER
 *   PADDLE_PRICE_BUNDLE_PRO
 *   PADDLE_PRICE_BUNDLE_BUSINESS
 *   PADDLE_PRICE_AIBUILDER_STARTER   (if selling AIBuilder via Paddle)
 *   PADDLE_PRICE_AIBUILDER_PRO
 */

const express = require('express');
const router = express.Router();
const crypto = require('crypto');
const User = require('../models/User');
const { authMiddleware: requireAuth } = require('./auth');

const PADDLE_API_KEY = process.env.PADDLE_API_KEY || '';
const PADDLE_WEBHOOK_SECRET = process.env.PADDLE_WEBHOOK_SECRET || '';
const PADDLE_ENV = process.env.PADDLE_ENV || 'sandbox';
const PADDLE_BASE = PADDLE_ENV === 'production'
  ? 'https://api.paddle.com'
  : 'https://sandbox-api.paddle.com';

// ─── Price ID → plan name map ─────────────────────────────────────────────────
const PRICE_TO_PLAN = {
  [process.env.PADDLE_PRICE_MARKETING_BASIC]:    'basic',
  [process.env.PADDLE_PRICE_MARKETING_PRO]:      'pro',
  [process.env.PADDLE_PRICE_MARKETING_BUSINESS]: 'business',
  [process.env.PADDLE_PRICE_BUNDLE_STARTER]:     'bundle_starter',
  [process.env.PADDLE_PRICE_BUNDLE_PRO]:         'bundle_pro',
  [process.env.PADDLE_PRICE_BUNDLE_BUSINESS]:    'bundle_business',
  [process.env.PADDLE_PRICE_AIBUILDER_STARTER]:  'aibuilder_starter',
  [process.env.PADDLE_PRICE_AIBUILDER_PRO]:      'aibuilder_pro',
};

// ─── Verify Paddle webhook signature ─────────────────────────────────────────
function verifyWebhookSignature(rawBody, signatureHeader) {
  if (!PADDLE_WEBHOOK_SECRET) return true; // skip in dev
  try {
    const parts = {};
    signatureHeader.split(';').forEach(part => {
      const [k, v] = part.split('=');
      parts[k.trim()] = v?.trim();
    });
    const ts = parts['ts'];
    const h1 = parts['h1'];
    if (!ts || !h1) return false;

    const signed = `${ts}:${rawBody.toString()}`;
    const expected = crypto
      .createHmac('sha256', PADDLE_WEBHOOK_SECRET)
      .update(signed)
      .digest('hex');
    return crypto.timingSafeEqual(Buffer.from(h1), Buffer.from(expected));
  } catch {
    return false;
  }
}

// ─── AIBuilder credits per plan ───────────────────────────────────────────────
const AIBUILDER_CREDITS = { starter: 100, pro: 350 };

// ─── Determine which plan field to update based on plan name ──────────────────
function getPlanUpdates(planName) {
  if (!planName) return {};

  if (planName.startsWith('bundle_')) {
    // Bundle: includes both AIBuilder + Marketing
    const marketingLevel = planName.replace('bundle_', ''); // starter/pro/business
    const aiLevel = marketingLevel === 'starter' ? 'starter' : 'pro';
    const updates = {
      marketing_plan: planName,
      plan: aiLevel,
    };
    if (AIBUILDER_CREDITS[aiLevel]) {
      updates.credits = AIBUILDER_CREDITS[aiLevel];
      updates.creditsLastReset = new Date();
    }
    return updates;
  }

  if (planName.startsWith('aibuilder_')) {
    // AIBuilder only
    const level = planName.replace('aibuilder_', ''); // starter/pro
    const updates = { plan: level };
    if (AIBUILDER_CREDITS[level]) {
      updates.credits = AIBUILDER_CREDITS[level];
      updates.creditsLastReset = new Date();
    }
    return updates;
  }

  // Marketing only
  return { marketing_plan: planName };
}

// ─── Paddle API helper ────────────────────────────────────────────────────────
async function paddleRequest(endpoint, method = 'GET', body = null) {
  const opts = {
    method,
    headers: {
      'Authorization': `Bearer ${PADDLE_API_KEY}`,
      'Content-Type': 'application/json',
    },
  };
  if (body) opts.body = JSON.stringify(body);
  const res = await fetch(`${PADDLE_BASE}${endpoint}`, opts);
  return res.json();
}

// ─── POST /api/paddle/webhook ─────────────────────────────────────────────────
// Must be registered BEFORE express.json() — uses raw body
router.post('/webhook', async (req, res) => {
  const sig = req.headers['paddle-signature'] || '';
  const rawBody = req.body; // raw buffer (registered with express.raw())

  if (PADDLE_WEBHOOK_SECRET && !verifyWebhookSignature(rawBody, sig)) {
    console.warn('⚠️ Paddle webhook signature invalid');
    return res.status(400).json({ error: 'Invalid signature' });
  }

  let event;
  try {
    event = JSON.parse(rawBody.toString());
  } catch {
    return res.status(400).json({ error: 'Invalid JSON' });
  }

  const eventType = event.event_type;
  const data = event.data || {};
  const customData = data.custom_data || {};
  const userId = customData.user_id;

  console.log(`📦 Paddle event: ${eventType} | user: ${userId}`);

  try {
    if (eventType === 'subscription.created' || eventType === 'subscription.updated') {
      const priceId = data.items?.[0]?.price?.id;
      const planName = PRICE_TO_PLAN[priceId] || null;
      const subscriptionId = data.id;

      if (userId && planName) {
        const updates = getPlanUpdates(planName);
        await User.findByIdAndUpdate(userId, {
          ...updates,
          paddleSubscriptionId: subscriptionId,
          subscriptionStatus: 'active',
        });
        console.log(`✅ User ${userId} upgraded to ${planName}`);
      }
    }

    if (eventType === 'subscription.canceled' || eventType === 'subscription.paused') {
      if (userId) {
        // Determine what was canceled to reset the right plan(s)
        const priceId = data.items?.[0]?.price?.id;
        const planName = PRICE_TO_PLAN[priceId] || null;
        const resetUpdates = { subscriptionStatus: 'canceled', paddleSubscriptionId: null };
        if (!planName || planName.startsWith('bundle_')) {
          // Bundle or unknown: reset both
          resetUpdates.plan = 'free';
          resetUpdates.marketing_plan = 'free';
        } else if (planName.startsWith('aibuilder_')) {
          resetUpdates.plan = 'free';
        } else {
          // Marketing only
          resetUpdates.marketing_plan = 'free';
        }
        await User.findByIdAndUpdate(userId, resetUpdates);
        console.log(`❌ User ${userId} subscription canceled → free (was: ${planName})`);
      }
    }

    if (eventType === 'transaction.completed') {
      // One-time payment (if applicable)
      console.log(`💳 Transaction completed for user ${userId}`);
    }

  } catch (e) {
    console.error('Paddle webhook processing error:', e.message);
  }

  res.json({ ok: true });
});

// ─── GET /api/paddle/subscription ────────────────────────────────────────────
// Returns current subscription info for the logged-in user
router.get('/subscription', requireAuth, async (req, res) => {
  try {
    const user = await User.findById(req.user.id).select('marketing_plan plan paddleSubscriptionId subscriptionStatus');
    if (!user) return res.status(404).json({ error: 'User not found' });

    if (!user.paddleSubscriptionId) {
      return res.json({ subscription: null, marketing_plan: user.marketing_plan || 'free' });
    }

    // Fetch live subscription data from Paddle
    const paddle = await paddleRequest(`/subscriptions/${user.paddleSubscriptionId}`);
    res.json({
      subscription: paddle.data || null,
      marketing_plan: user.marketing_plan || 'free',
      status: user.subscriptionStatus,
    });
  } catch (e) {
    console.error('Get subscription error:', e.message);
    res.status(500).json({ error: 'Failed to fetch subscription' });
  }
});

// ─── POST /api/paddle/cancel ─────────────────────────────────────────────────
router.post('/cancel', requireAuth, async (req, res) => {
  try {
    const user = await User.findById(req.user.id).select('paddleSubscriptionId');
    if (!user?.paddleSubscriptionId) {
      return res.status(400).json({ error: 'No active subscription' });
    }

    // Cancel at end of billing period
    const result = await paddleRequest(
      `/subscriptions/${user.paddleSubscriptionId}/cancel`,
      'POST',
      { effective_from: 'next_billing_period' }
    );

    await User.findByIdAndUpdate(req.user.id, { subscriptionStatus: 'cancel_scheduled' });
    res.json({ ok: true, result: result.data });
  } catch (e) {
    console.error('Cancel subscription error:', e.message);
    res.status(500).json({ error: 'Failed to cancel subscription' });
  }
});

// ─── POST /api/paddle/update-payment ─────────────────────────────────────────
// Returns a Paddle update payment URL for the user to update their card
router.post('/update-payment', requireAuth, async (req, res) => {
  try {
    const user = await User.findById(req.user.id).select('paddleSubscriptionId');
    if (!user?.paddleSubscriptionId) {
      return res.status(400).json({ error: 'No active subscription' });
    }

    const result = await paddleRequest(
      `/subscriptions/${user.paddleSubscriptionId}/update-payment-method-transaction`,
      'GET'
    );

    res.json({ url: result.data?.checkout?.url || null });
  } catch (e) {
    res.status(500).json({ error: 'Failed to get update payment URL' });
  }
});

// ─── GET /api/paddle/prices ───────────────────────────────────────────────────
// Returns configured price IDs for the frontend Paddle.js checkout
router.get('/prices', (req, res) => {
  res.json({
    marketing: {
      basic:    process.env.PADDLE_PRICE_MARKETING_BASIC    || null,
      pro:      process.env.PADDLE_PRICE_MARKETING_PRO      || null,
      business: process.env.PADDLE_PRICE_MARKETING_BUSINESS || null,
    },
    bundle: {
      starter:  process.env.PADDLE_PRICE_BUNDLE_STARTER     || null,
      pro:      process.env.PADDLE_PRICE_BUNDLE_PRO         || null,
      business: process.env.PADDLE_PRICE_BUNDLE_BUSINESS    || null,
    },
    aibuilder: {
      starter:  process.env.PADDLE_PRICE_AIBUILDER_STARTER  || null,
      pro:      process.env.PADDLE_PRICE_AIBUILDER_PRO      || null,
    },
    env: PADDLE_ENV,
  });
});

module.exports = router;
