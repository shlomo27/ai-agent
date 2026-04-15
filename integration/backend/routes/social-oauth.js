/**
 * social-oauth.js — OAuth flow for connecting social media platforms
 *
 * Supports: Facebook, Instagram (via Facebook), LinkedIn, Twitter/X, TikTok
 *
 * Flow:
 *  1. Frontend calls GET /api/social/connect/:platform → returns OAuth URL
 *  2. User is redirected to platform's auth page
 *  3. Platform redirects back to /api/social/callback/:platform?code=...
 *  4. We exchange code for access token, store in user.socialTokens
 *  5. Frontend is redirected to /advertising with success param
 *
 * Setup in server.js:
 *   const socialOAuthRouter = require('./routes/social-oauth');
 *   app.use('/api/social', socialOAuthRouter);
 *
 * Required env vars per platform:
 *
 *   Facebook / Instagram:
 *     FACEBOOK_APP_ID
 *     FACEBOOK_APP_SECRET
 *     FACEBOOK_REDIRECT_URI=https://ilmariai.com/api/social/callback/facebook
 *
 *   LinkedIn:
 *     LINKEDIN_CLIENT_ID
 *     LINKEDIN_CLIENT_SECRET
 *     LINKEDIN_REDIRECT_URI=https://ilmariai.com/api/social/callback/linkedin
 *
 *   Twitter/X:
 *     TWITTER_CLIENT_ID
 *     TWITTER_CLIENT_SECRET
 *     TWITTER_REDIRECT_URI=https://ilmariai.com/api/social/callback/twitter
 *
 *   TikTok:
 *     TIKTOK_CLIENT_KEY
 *     TIKTOK_CLIENT_SECRET
 *     TIKTOK_REDIRECT_URI=https://ilmariai.com/api/social/callback/tiktok
 */

const express = require('express');
const router = express.Router();
const crypto = require('crypto');
const User = require('../models/User');
const { authMiddleware: requireAuth } = require('./auth');

const FRONTEND_URL = process.env.FRONTEND_URL || 'https://ilmariai.com';

// ─── OAuth config per platform ────────────────────────────────────────────────
const PLATFORM_CONFIG = {
  facebook: {
    authUrl: 'https://www.facebook.com/v19.0/dialog/oauth',
    tokenUrl: 'https://graph.facebook.com/v19.0/oauth/access_token',
    clientId: process.env.FACEBOOK_APP_ID,
    clientSecret: process.env.FACEBOOK_APP_SECRET,
    redirectUri: process.env.FACEBOOK_REDIRECT_URI,
    scope: 'pages_manage_posts,pages_read_engagement,instagram_basic,instagram_content_publish,business_management',
  },
  instagram: {
    // Instagram uses Facebook's OAuth but with different scopes
    authUrl: 'https://www.facebook.com/v19.0/dialog/oauth',
    tokenUrl: 'https://graph.facebook.com/v19.0/oauth/access_token',
    clientId: process.env.FACEBOOK_APP_ID,
    clientSecret: process.env.FACEBOOK_APP_SECRET,
    redirectUri: process.env.FACEBOOK_REDIRECT_URI || process.env.INSTAGRAM_REDIRECT_URI,
    scope: 'instagram_basic,instagram_content_publish,pages_show_list,business_management',
  },
  linkedin: {
    authUrl: 'https://www.linkedin.com/oauth/v2/authorization',
    tokenUrl: 'https://www.linkedin.com/oauth/v2/accessToken',
    clientId: process.env.LINKEDIN_CLIENT_ID,
    clientSecret: process.env.LINKEDIN_CLIENT_SECRET,
    redirectUri: process.env.LINKEDIN_REDIRECT_URI,
    scope: 'w_member_social,r_liteprofile',
  },
  twitter: {
    authUrl: 'https://twitter.com/i/oauth2/authorize',
    tokenUrl: 'https://api.twitter.com/2/oauth2/token',
    clientId: process.env.TWITTER_CLIENT_ID,
    clientSecret: process.env.TWITTER_CLIENT_SECRET,
    redirectUri: process.env.TWITTER_REDIRECT_URI,
    scope: 'tweet.read tweet.write users.read offline.access',
  },
  tiktok: {
    authUrl: 'https://www.tiktok.com/v2/auth/authorize',
    tokenUrl: 'https://open.tiktokapis.com/v2/oauth/token/',
    clientId: process.env.TIKTOK_CLIENT_KEY,
    clientSecret: process.env.TIKTOK_CLIENT_SECRET,
    redirectUri: process.env.TIKTOK_REDIRECT_URI,
    scope: 'user.info.basic,video.publish',
  },
};

// Temporary state store (in production use Redis or DB)
const oauthStates = new Map(); // state → { userId, platform, createdAt }

// Clean expired states every 10 min
setInterval(() => {
  const now = Date.now();
  for (const [k, v] of oauthStates) {
    if (now - v.createdAt > 10 * 60 * 1000) oauthStates.delete(k);
  }
}, 10 * 60 * 1000);

// ─── GET /api/social/connect/:platform ───────────────────────────────────────
// Returns the OAuth URL to redirect the user to
router.get('/connect/:platform', requireAuth, (req, res) => {
  const { platform } = req.params;
  const config = PLATFORM_CONFIG[platform];

  if (!config) {
    return res.status(400).json({ error: `Platform "${platform}" not supported` });
  }
  if (!config.clientId) {
    return res.status(503).json({ error: `${platform} OAuth not configured on server` });
  }

  const state = crypto.randomBytes(20).toString('hex');
  oauthStates.set(state, { userId: req.user.id, platform, createdAt: Date.now() });

  const params = new URLSearchParams({
    client_id: config.clientId,
    redirect_uri: config.redirectUri,
    scope: config.scope,
    response_type: 'code',
    state,
  });

  // Force Facebook to show the full permissions dialog even if user previously
  // authorized the app with fewer permissions (prevents silent "Reconnect" reuse)
  if (platform === 'facebook' || platform === 'instagram') {
    params.set('auth_type', 'rerequest');
  }

  // Twitter uses PKCE
  if (platform === 'twitter') {
    params.set('code_challenge_method', 'plain');
    params.set('code_challenge', state);
  }

  res.json({ url: `${config.authUrl}?${params.toString()}` });
});

// ─── GET /api/social/callback/:platform ──────────────────────────────────────
// OAuth callback — called by the social platform after user grants access
router.get('/callback/:platform', async (req, res) => {
  const { platform } = req.params;
  const { code, state, error } = req.query;

  if (error) {
    return res.redirect(`${FRONTEND_URL}/advertising?social_error=${encodeURIComponent(error)}`);
  }

  const stateData = oauthStates.get(state);
  if (!stateData || stateData.platform !== platform) {
    return res.redirect(`${FRONTEND_URL}/advertising?social_error=invalid_state`);
  }
  oauthStates.delete(state);

  const config = PLATFORM_CONFIG[platform];

  try {
    // Exchange code for access token
    let tokenData;

    if (platform === 'twitter') {
      const creds = Buffer.from(`${config.clientId}:${config.clientSecret}`).toString('base64');
      const r = await fetch(config.tokenUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded', Authorization: `Basic ${creds}` },
        body: new URLSearchParams({ code, grant_type: 'authorization_code', redirect_uri: config.redirectUri, code_verifier: state }),
      });
      tokenData = await r.json();
    } else if (platform === 'tiktok') {
      const r = await fetch(config.tokenUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: new URLSearchParams({ client_key: config.clientId, client_secret: config.clientSecret, code, grant_type: 'authorization_code', redirect_uri: config.redirectUri }),
      });
      tokenData = await r.json();
    } else {
      const r = await fetch(config.tokenUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: new URLSearchParams({ client_id: config.clientId, client_secret: config.clientSecret, code, redirect_uri: config.redirectUri, grant_type: 'authorization_code' }),
      });
      tokenData = await r.json();
    }

    const accessToken = tokenData.access_token;
    if (!accessToken) throw new Error('No access token in response');

    // For Facebook/Instagram: get page access token from /me/accounts
    // Page access tokens already include pages_manage_posts permission — no extra scope needed
    let pageId = null, pageName = null, pageAccessToken = null;
    if (platform === 'facebook' || platform === 'instagram') {
      const pagesRes = await fetch(
        `https://graph.facebook.com/v19.0/me/accounts?fields=id,name,access_token&access_token=${accessToken}`
      );
      const pagesData = await pagesRes.json();
      console.log(`[social-oauth] ${platform} pages response:`, JSON.stringify(pagesData).slice(0, 200));
      if (pagesData.data?.[0]) {
        pageId = pagesData.data[0].id;
        pageName = pagesData.data[0].name;
        pageAccessToken = pagesData.data[0].access_token || null; // page-level token with manage_posts
      }
    }

    const expiresAt = tokenData.expires_in
      ? new Date(Date.now() + tokenData.expires_in * 1000)
      : null;

    // Save token to user — prefer page access token for Facebook (has manage_posts)
    const user = await User.findById(stateData.userId);
    if (!user) throw new Error('User not found');

    await user.setSocialToken(platform, {
      accessToken: pageAccessToken || accessToken, // page token preferred
      refreshToken: tokenData.refresh_token || null,
      pageId,
      pageName,
      expiresAt,
    });

    console.log(`✅ ${platform} connected for user ${stateData.userId}`);
    res.redirect(`${FRONTEND_URL}/advertising?social_connected=${platform}`);

  } catch (e) {
    console.error(`OAuth callback error for ${platform}:`, e.message);
    res.redirect(`${FRONTEND_URL}/advertising?social_error=${encodeURIComponent(e.message)}`);
  }
});

// ─── GET /api/social/status ───────────────────────────────────────────────────
// Returns which platforms the user has connected
router.get('/status', requireAuth, async (req, res) => {
  try {
    const user = await User.findById(req.user.id).select('socialTokens');
    if (!user) return res.status(404).json({ error: 'User not found' });

    const connected = {};
    for (const token of user.socialTokens) {
      connected[token.platform] = {
        connected: true,
        pageName: token.pageName || null,
        connectedAt: token.connectedAt,
        expired: token.expiresAt ? token.expiresAt < new Date() : false,
      };
    }

    res.json({ connected });
  } catch (e) {
    res.status(500).json({ error: 'Failed to get status' });
  }
});

// ─── DELETE /api/social/disconnect/:platform ──────────────────────────────────
router.delete('/disconnect/:platform', requireAuth, async (req, res) => {
  try {
    const user = await User.findById(req.user.id);
    if (!user) return res.status(404).json({ error: 'User not found' });
    await user.removeSocialToken(req.params.platform);
    res.json({ ok: true, platform: req.params.platform });
  } catch (e) {
    res.status(500).json({ error: 'Failed to disconnect' });
  }
});

module.exports = router;
