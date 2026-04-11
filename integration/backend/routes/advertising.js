/**
 * advertising.js — Proxy routes between appify and the AI Advertising Agent.
 *
 * All routes require authentication (JWT).
 * The authenticated user's _id is used as the session_id in the AI Agent,
 * so conversation history and business profile persist across devices/sessions.
 *
 * Plan enforcement is handled here (Node.js side) before hitting the AI Agent.
 */

const express = require('express');
const router = express.Router();
const User = require('../models/User');

// Use auth middleware from routes/auth (has JWT_SECRET fallback — matches token signing)
const { authMiddleware: requireAuth } = require('./auth');

const AI_AGENT_URL = process.env.AI_AGENT_URL || 'https://ai-agent-production-bf7b.up.railway.app';

// ─── Plan feature map ─────────────────────────────────────────────────────────
// Defines which features are available per marketing plan
const PLAN_FEATURES = {
  free:           { scheduled_posts: 0,  ab_testing: false, translation: false, competitor_monitor: false, report: false },
  basic:          { scheduled_posts: 3,  ab_testing: false, translation: true,  competitor_monitor: false, report: false },
  pro:            { scheduled_posts: 20, ab_testing: true,  translation: true,  competitor_monitor: false, report: true  },
  business:       { scheduled_posts: -1, ab_testing: true,  translation: true,  competitor_monitor: true,  report: true  },
  bundle_starter: { scheduled_posts: 3,  ab_testing: false, translation: true,  competitor_monitor: false, report: false },
  bundle_pro:     { scheduled_posts: 20, ab_testing: true,  translation: true,  competitor_monitor: false, report: true  },
  bundle_business:{ scheduled_posts: -1, ab_testing: true,  translation: true,  competitor_monitor: true,  report: true  },
};

function getPlanFeatures(plan) {
  return PLAN_FEATURES[plan] || PLAN_FEATURES.free;
}

// ─── Proxy helper ─────────────────────────────────────────────────────────────
async function proxyToAgent(path, method, body, res, extraHeaders = {}) {
  try {
    const options = {
      method,
      headers: { 'Content-Type': 'application/json', ...extraHeaders },
    };
    if (body) options.body = JSON.stringify(body);

    const response = await fetch(`${AI_AGENT_URL}${path}`, options);
    const data = await response.json();
    res.status(response.status).json(data);
  } catch (error) {
    console.error('AI Agent proxy error:', error.message);
    res.status(500).json({ error: 'Failed to connect to AI Advertising Agent' });
  }
}

// ─── Auth + user enrichment middleware ────────────────────────────────────────
// Loads user from DB so we have plan info on req.advertising
async function loadUser(req, res, next) {
  try {
    const user = await User.findById(req.user.id).select('plan marketing_plan subscriptionStatus');
    if (!user) return res.status(404).json({ error: 'User not found' });

    // Determine effective marketing plan
    const marketingPlan = user.marketing_plan || 'free';
    req.advertising = {
      userId: String(user._id),
      plan: marketingPlan,
      features: getPlanFeatures(marketingPlan),
    };
    next();
  } catch (e) {
    console.error('loadUser error:', e.message);
    res.status(500).json({ error: 'Server error' });
  }
}

// Apply auth to all advertising routes
router.use(requireAuth, loadUser);

// ─── Chat ─────────────────────────────────────────────────────────────────────
router.post('/chat', (req, res) => {
  const body = {
    ...req.body,
    session_id: req.advertising.userId,   // use MongoDB _id as stable session key
    plan: req.advertising.plan,
    language: req.body.language || 'he',  // pass language preference
  };
  proxyToAgent('/api/chat', 'POST', body, res);
});

// ─── Platforms ────────────────────────────────────────────────────────────────
router.get('/platforms', (req, res) =>
  proxyToAgent('/api/platforms', 'GET', null, res)
);

router.post('/platforms/connect', (req, res) =>
  proxyToAgent('/api/platforms/connect', 'POST', req.body, res)
);

// ─── Posts ────────────────────────────────────────────────────────────────────
router.post('/posts', (req, res) =>
  proxyToAgent('/api/posts', 'POST', req.body, res)
);

// ─── Campaigns ────────────────────────────────────────────────────────────────
router.post('/campaigns', (req, res) =>
  proxyToAgent('/api/campaigns', 'POST', req.body, res)
);

// ─── Analytics ────────────────────────────────────────────────────────────────
router.get('/analytics', (req, res) =>
  proxyToAgent(`/api/analytics?session_id=${req.advertising.userId}`, 'GET', null, res)
);

// ─── Recommendations ─────────────────────────────────────────────────────────
router.get('/recommendations', (req, res) =>
  proxyToAgent(`/api/recommendations?session_id=${req.advertising.userId}`, 'GET', null, res)
);

// ─── Business Profile ────────────────────────────────────────────────────────
router.get('/profile', (req, res) =>
  proxyToAgent(`/api/profile/${req.advertising.userId}`, 'GET', null, res)
);

router.delete('/profile', (req, res) =>
  proxyToAgent(`/api/profile/${req.advertising.userId}`, 'DELETE', null, res)
);

// ─── Scheduled Posts ─────────────────────────────────────────────────────────
router.get('/scheduled', (req, res) =>
  proxyToAgent(`/api/scheduled/${req.advertising.userId}`, 'GET', null, res)
);

router.delete('/scheduled/:jobId', (req, res) =>
  proxyToAgent(`/api/scheduled/${req.advertising.userId}/${req.params.jobId}`, 'DELETE', null, res)
);

// ─── Notifications ────────────────────────────────────────────────────────────
router.get('/notifications', (req, res) =>
  proxyToAgent(`/api/notifications/${req.advertising.userId}`, 'GET', null, res)
);

router.post('/notifications/read', (req, res) =>
  proxyToAgent(`/api/notifications/${req.advertising.userId}/read`, 'POST', null, res)
);

// ─── Usage stats ─────────────────────────────────────────────────────────────
router.get('/usage', (req, res) =>
  proxyToAgent(`/api/usage/${req.advertising.userId}?plan=${req.advertising.plan}`, 'GET', null, res)
);

// ─── Weekly Report (Pro+ only) ────────────────────────────────────────────────
router.get('/report', (req, res) => {
  if (!req.advertising.features.report) {
    return res.status(403).json({
      error: 'תכונה זו זמינה בתוכנית Pro ומעלה',
      upgrade_required: true,
      current_plan: req.advertising.plan,
    });
  }
  proxyToAgent(`/api/report/${req.advertising.userId}`, 'GET', null, res);
});

// ─── Plan info endpoint ───────────────────────────────────────────────────────
// Used by frontend to know what features are available
router.get('/plan', (req, res) => {
  res.json({
    plan: req.advertising.plan,
    features: req.advertising.features,
  });
});

// ─── CRM leads ────────────────────────────────────────────────────────────────
router.get('/crm', (req, res) =>
  proxyToAgent(`/api/crm/${req.advertising.userId}`, 'GET', null, res)
);

// ─── Audit log ────────────────────────────────────────────────────────────────
router.get('/audit', (req, res) =>
  proxyToAgent(`/api/audit/${req.advertising.userId}`, 'GET', null, res)
);

// ─── Weekly email (manual trigger, Pro+ only) ─────────────────────────────────
router.post('/send-weekly-report', async (req, res) => {
  if (!req.advertising.features.report) {
    return res.status(403).json({
      error: 'תכונה זו זמינה בתוכנית Pro ומעלה',
      upgrade_required: true,
      current_plan: req.advertising.plan,
    });
  }
  try {
    const {
      fetchWeeklyReportData,
      buildEmailHtml,
      sendEmailViaResend,
    } = require('../services/weeklyEmailReport');

    const user = await User.findById(req.advertising.userId).select('email').lean();
    if (!user || !user.email) {
      return res.status(400).json({ error: 'אין כתובת מייל מוגדרת' });
    }

    const data = await fetchWeeklyReportData(req.advertising.userId);
    if (!data || !data.report) {
      return res.status(500).json({ error: 'לא ניתן לייצר דוח — נסה שוב' });
    }

    const html = buildEmailHtml(data);
    const ok = await sendEmailViaResend(user.email, data.email_subject, html);

    if (!ok) {
      return res.status(500).json({ error: 'שגיאה בשליחת המייל' });
    }

    return res.json({
      message: 'דוח שבועי נשלח בהצלחה',
      email: user.email,
      report_period: data.report?.period,
    });
  } catch (err) {
    console.error('[send-weekly-report]', err.message);
    res.status(500).json({ error: 'שגיאה בשליחת הדוח' });
  }
});

// ─── Chat history ─────────────────────────────────────────────────────────────
router.get('/chat/history', (req, res) =>
  proxyToAgent(`/api/chat/${req.advertising.userId}/history`, 'GET', null, res)
);

router.delete('/chat/history', (req, res) =>
  proxyToAgent(`/api/chat/${req.advertising.userId}`, 'DELETE', null, res)
);

module.exports = router;
