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
    scope: 'pages_manage_posts,pages_read_engagement,business_management',
  },
  instagram: {
    authUrl: 'https://www.facebook.com/v19.0/dialog/oauth',
    tokenUrl: 'https://graph.facebook.com/v19.0/oauth/access_token',
    clientId: process.env.FACEBOOK_APP_ID,
    clientSecret: process.env.FACEBOOK_APP_SECRET,
    redirectUri: process.env.FACEBOOK_REDIRECT_URI || process.env.INSTAGRAM_REDIRECT_URI,
    scope: 'pages_show_list,pages_read_engagement,business_management',
  },
  linkedin: {
    authUrl: 'https://www.linkedin.com/oauth/v2/authorization',
    tokenUrl: 'https://www.linkedin.com/oauth/v2/accessToken',
    clientId: process.env.LINKEDIN_CLIENT_ID,
    clientSecret: process.env.LINKEDIN_CLIENT_SECRET,
    redirectUri: process.env.LINKEDIN_REDIRECT_URI,
    // w_member_social — post on behalf of member
    // r_basicprofile / profile — read name/headline
    // offline_access — get refresh token (365 days) so we can auto-renew the 60-day access token
    // r_organization_social — company page analytics (requires Marketing API partner)
    scope: 'openid profile email w_member_social offline_access',
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
    scope: 'user.info.basic',  // video.publish requires App Review — add after approval
  },
  youtube: {
    authUrl: 'https://accounts.google.com/o/oauth2/v2/auth',
    tokenUrl: 'https://oauth2.googleapis.com/token',
    clientId: process.env.YOUTUBE_CLIENT_ID,
    clientSecret: process.env.YOUTUBE_CLIENT_SECRET,
    redirectUri: process.env.YOUTUBE_REDIRECT_URI,
    scope: 'https://www.googleapis.com/auth/youtube.upload https://www.googleapis.com/auth/youtube.readonly openid email profile',
  },
  reddit: {
    authUrl: 'https://www.reddit.com/api/v1/authorize',
    tokenUrl: 'https://www.reddit.com/api/v1/access_token',
    clientId: process.env.REDDIT_CLIENT_ID,
    clientSecret: process.env.REDDIT_CLIENT_SECRET,
    redirectUri: process.env.REDDIT_REDIRECT_URI,
    scope: 'submit identity read',
  },
};

// ─── Stateless signed state (works across multiple server instances) ──────────
const STATE_SECRET = process.env.SESSION_SECRET || process.env.JWT_SECRET || 'ilmariai-oauth-secret';

function createState(userId, platform, extra) {
  const payload = extra
    ? `${userId}:${platform}:${Date.now()}:${extra}`
    : `${userId}:${platform}:${Date.now()}`;
  const sig = crypto.createHmac('sha256', STATE_SECRET).update(payload).digest('hex').slice(0, 24);
  return Buffer.from(payload).toString('base64url') + '.' + sig;
}

function verifyState(state, expectedPlatform) {
  try {
    const dot = state.lastIndexOf('.');
    if (dot === -1) return null;
    const b64 = state.slice(0, dot);
    const sig = state.slice(dot + 1);
    const payload = Buffer.from(b64, 'base64url').toString();
    const expectedSig = crypto.createHmac('sha256', STATE_SECRET).update(payload).digest('hex').slice(0, 24);
    if (sig !== expectedSig) return null;
    const parts = payload.split(':');
    if (parts.length < 3) return null;
    const [userId, platform, ts, ...rest] = parts;
    if (platform !== expectedPlatform) return null;
    if (Date.now() - parseInt(ts) > 15 * 60 * 1000) return null; // 15 min expiry
    return { userId, platform, extra: rest.length ? rest.join(':') : null };
  } catch {
    return null;
  }
}

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

  // Twitter PKCE: generate a proper random code_verifier, embed it in the signed state
  let codeVerifier = null;
  if (platform === 'twitter') {
    codeVerifier = crypto.randomBytes(32).toString('base64url');
  }

  const state = createState(req.user.id, platform, codeVerifier);

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

  // Twitter PKCE — send the random verifier as the code_challenge (plain method)
  if (platform === 'twitter') {
    params.set('code_challenge_method', 'plain');
    params.set('code_challenge', codeVerifier);
  }

  // TikTok uses client_key instead of client_id in the auth URL
  if (platform === 'tiktok') {
    params.delete('client_id');
    params.set('client_key', config.clientId);
  }

  // YouTube needs offline access for refresh token
  if (platform === 'youtube') {
    params.set('access_type', 'offline');
    params.set('prompt', 'consent');
  }

  // Reddit requires duration=permanent for refresh token
  if (platform === 'reddit') {
    params.set('duration', 'permanent');
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

  const stateData = verifyState(state, platform);
  if (!stateData) {
    return res.redirect(`${FRONTEND_URL}/advertising?social_error=invalid_state`);
  }

  const config = PLATFORM_CONFIG[platform];

  try {
    // Exchange code for access token
    let tokenData;

    if (platform === 'twitter') {
      const pkceVerifier = stateData.extra;
      if (!pkceVerifier) throw new Error('Missing PKCE code verifier — please try connecting again');
      const encodedId = encodeURIComponent(config.clientId);
      const encodedSecret = encodeURIComponent(config.clientSecret);
      const creds = Buffer.from(`${encodedId}:${encodedSecret}`).toString('base64');
      const r = await fetch(config.tokenUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded', Authorization: `Basic ${creds}` },
        body: new URLSearchParams({ code, grant_type: 'authorization_code', redirect_uri: config.redirectUri, code_verifier: pkceVerifier }),
      });
      tokenData = await r.json();
      console.log(`[social-oauth] Twitter token response status:`, r.status);
    } else if (platform === 'tiktok') {
      const r = await fetch(config.tokenUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: new URLSearchParams({ client_key: config.clientId, client_secret: config.clientSecret, code, grant_type: 'authorization_code', redirect_uri: config.redirectUri }),
      });
      tokenData = await r.json();
    } else if (platform === 'reddit') {
      // Reddit uses Basic auth with URL-encoded credentials
      const encodedId = encodeURIComponent(config.clientId);
      const encodedSecret = encodeURIComponent(config.clientSecret);
      const creds = Buffer.from(`${encodedId}:${encodedSecret}`).toString('base64');
      const r = await fetch(config.tokenUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded', Authorization: `Basic ${creds}`, 'User-Agent': 'ilmariai-agent/1.0' },
        body: new URLSearchParams({ code, grant_type: 'authorization_code', redirect_uri: config.redirectUri }),
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
    if (!accessToken) {
      const detail = tokenData.error_description || tokenData.error || JSON.stringify(tokenData).slice(0, 120);
      throw new Error(`No access token: ${detail}`);
    }

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

    // Attempt silent refresh for any expired tokens that have a refresh token
    for (const token of user.socialTokens) {
      if (token.expiresAt && token.expiresAt < new Date() && token.refreshToken) {
        await refreshTokenIfNeeded(user, token.platform).catch(() => {});
      }
    }
    // Re-fetch after potential refresh
    await user.populate && user.populate('socialTokens');
    const freshUser = await User.findById(req.user.id).select('socialTokens');

    const connected = {};
    for (const token of (freshUser?.socialTokens || [])) {
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

// ─── Token refresh helper (called by advertising.js before each agent request) ─
async function refreshTokenIfNeeded(user, platformName) {
  const entry = user.socialTokens.find(t => t.platform === platformName);
  if (!entry?.accessToken) return null;

  // Refresh if within 5 minutes of expiry or already expired
  const needsRefresh = entry.expiresAt && entry.expiresAt < new Date(Date.now() + 5 * 60 * 1000);
  if (!needsRefresh) return entry.accessToken;

  if (!entry.refreshToken) {
    console.log(`[token-refresh] No refresh token for ${platformName}`);
    return entry.accessToken;
  }

  const cfg = PLATFORM_CONFIG[platformName];
  if (!cfg) return entry.accessToken;

  try {
    let newData;
    if (platformName === 'twitter') {
      const creds = Buffer.from(`${encodeURIComponent(cfg.clientId)}:${encodeURIComponent(cfg.clientSecret)}`).toString('base64');
      const r = await fetch(cfg.tokenUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded', Authorization: `Basic ${creds}` },
        body: new URLSearchParams({ grant_type: 'refresh_token', refresh_token: entry.refreshToken, client_id: cfg.clientId }),
      });
      newData = await r.json();
    } else if (platformName === 'reddit') {
      const creds = Buffer.from(`${encodeURIComponent(cfg.clientId)}:${encodeURIComponent(cfg.clientSecret)}`).toString('base64');
      const r = await fetch(cfg.tokenUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded', Authorization: `Basic ${creds}`, 'User-Agent': 'ilmariai-agent/1.0' },
        body: new URLSearchParams({ grant_type: 'refresh_token', refresh_token: entry.refreshToken }),
      });
      newData = await r.json();
    } else {
      // YouTube, LinkedIn, Facebook — standard OAuth2 refresh
      const r = await fetch(cfg.tokenUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: new URLSearchParams({ grant_type: 'refresh_token', refresh_token: entry.refreshToken, client_id: cfg.clientId, client_secret: cfg.clientSecret }),
      });
      newData = await r.json();
    }

    if (newData?.access_token) {
      const expiresAt = newData.expires_in ? new Date(Date.now() + newData.expires_in * 1000) : null;
      await user.setSocialToken(platformName, {
        accessToken: newData.access_token,
        refreshToken: newData.refresh_token || entry.refreshToken,
        pageId: entry.pageId,
        pageName: entry.pageName,
        expiresAt,
      });
      console.log(`✅ [token-refresh] Refreshed ${platformName} for user ${user._id}`);
      return newData.access_token;
    }
    console.warn(`[token-refresh] No access_token in response for ${platformName}:`, JSON.stringify(newData).slice(0, 120));
  } catch (e) {
    console.error(`[token-refresh] Error refreshing ${platformName}:`, e.message);
  }
  return entry.accessToken;
}

router.refreshTokenIfNeeded = refreshTokenIfNeeded;
module.exports = router;
