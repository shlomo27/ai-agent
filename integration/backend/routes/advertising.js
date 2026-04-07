const express = require('express');
const router = express.Router();

const AI_AGENT_URL = process.env.AI_AGENT_URL || 'https://ai-agent-production-bf7b.up.railway.app';

async function proxyToAgent(path, method, body, res) {
  try {
    const options = {
      method,
      headers: { 'Content-Type': 'application/json' },
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

// Chat with the AI agent
router.post('/chat', (req, res) => proxyToAgent('/api/chat', 'POST', req.body, res));

// Get connected platforms
router.get('/platforms', (req, res) => proxyToAgent('/api/platforms', 'GET', null, res));

// Connect a platform
router.post('/platforms/connect', (req, res) => proxyToAgent('/api/platforms/connect', 'POST', req.body, res));

// Create a post
router.post('/posts', (req, res) => proxyToAgent('/api/posts', 'POST', req.body, res));

// Create a campaign
router.post('/campaigns', (req, res) => proxyToAgent('/api/campaigns', 'POST', req.body, res));

// Get analytics
router.get('/analytics', (req, res) => proxyToAgent('/api/analytics', 'GET', null, res));

// Get recommendations
router.get('/recommendations', (req, res) => proxyToAgent('/api/recommendations', 'GET', null, res));

// Business profile
router.get('/profile/:sessionId', (req, res) => proxyToAgent(`/api/profile/${req.params.sessionId}`, 'GET', null, res));
router.delete('/profile/:sessionId', (req, res) => proxyToAgent(`/api/profile/${req.params.sessionId}`, 'DELETE', null, res));

// Scheduled posts
router.get('/scheduled/:sessionId', (req, res) => proxyToAgent(`/api/scheduled/${req.params.sessionId}`, 'GET', null, res));
router.delete('/scheduled/:sessionId/:jobId', (req, res) => proxyToAgent(`/api/scheduled/${req.params.sessionId}/${req.params.jobId}`, 'DELETE', null, res));

// Notifications
router.get('/notifications/:sessionId', (req, res) => proxyToAgent(`/api/notifications/${req.params.sessionId}`, 'GET', null, res));
router.post('/notifications/:sessionId/read', (req, res) => proxyToAgent(`/api/notifications/${req.params.sessionId}/read`, 'POST', null, res));

// Usage stats
router.get('/usage/:sessionId', (req, res) => proxyToAgent(`/api/usage/${req.params.sessionId}`, 'GET', null, res));

// Weekly report
router.get('/report/:sessionId', (req, res) => proxyToAgent(`/api/report/${req.params.sessionId}`, 'GET', null, res));

module.exports = router;
