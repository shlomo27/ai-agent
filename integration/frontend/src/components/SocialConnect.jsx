/**
 * SocialConnect — panel for connecting / disconnecting social media accounts.
 *
 * Placed on the /advertising page. On mount it reads URL params
 * (?social_connected=facebook or ?social_error=...) so the user sees
 * feedback after returning from OAuth.
 *
 * API endpoints (all go through appify → require Bearer token):
 *   GET  /api/social/status            — which platforms are connected
 *   GET  /api/social/connect/:platform — returns { url } to redirect to
 *   DELETE /api/social/disconnect/:platform
 */
import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';

const PLATFORMS = [
  { id: 'facebook',  label: 'Facebook',  icon: '📘', color: '#1877f2' },
  { id: 'instagram', label: 'Instagram', icon: '📸', color: '#e1306c' },
  { id: 'twitter',   label: 'Twitter/X', icon: '🐦', color: '#1da1f2' },
  { id: 'linkedin',  label: 'LinkedIn',  icon: '💼', color: '#0077b5' },
  { id: 'tiktok',    label: 'TikTok',    icon: '🎵', color: '#010101' },
];

const TEXT = {
  he: {
    title: '🔗 חיבור פלטפורמות',
    connect: 'חבר',
    disconnect: 'נתק',
    connected: 'מחובר',
    disconnected: 'לא מחובר',
    expired: 'פג תוקף',
    connecting: 'מחבר...',
    successMsg: (p) => `✅ ${p} חוברה בהצלחה!`,
    errorMsg: (e) => `❌ שגיאה: ${e}`,
    noPlatformsBanner: '⚠️ כדי שה-AI יוכל לפרסם בשמך — חבר לפחות פלטפורמה אחת. לחץ "חבר" ליד הפלטפורמה הרצויה, אשר גישה, וה-AI יתחיל לפרסם אוטומטית.',
    dir: 'rtl',
  },
  en: {
    title: '🔗 Connect Platforms',
    connect: 'Connect',
    disconnect: 'Disconnect',
    connected: 'Connected',
    disconnected: 'Not connected',
    expired: 'Token expired',
    connecting: 'Connecting...',
    successMsg: (p) => `✅ ${p} connected successfully!`,
    errorMsg: (e) => `❌ Error: ${e}`,
    noPlatformsBanner: '⚠️ To let the AI post on your behalf — connect at least one platform. Click "Connect" next to the platform, approve access, and the AI will start posting automatically.',
    dir: 'ltr',
  },
};

export default function SocialConnect({ language = 'he' }) {
  const { token } = useAuth();
  const t = TEXT[language] || TEXT.he;

  const [status, setStatus] = useState({});   // { facebook: { connected, pageName, expired }, ... }
  const [loading, setLoading] = useState({});  // { facebook: true, ... }
  const [toast, setToast] = useState(null);    // { msg, ok }

  const authFetch = useCallback((url, opts = {}) =>
    fetch(url, {
      ...opts,
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
        ...(opts.headers || {}),
      },
    }), [token]);

  // ── Load connection status ──────────────────────────────────────────────────
  const loadStatus = useCallback(async () => {
    try {
      const res = await authFetch('/api/social/status');
      const data = await res.json();
      setStatus(data.connected || {});
    } catch {
      // silently ignore — user may not have any connections yet
    }
  }, [authFetch]);

  useEffect(() => { loadStatus(); }, [loadStatus]);

  // ── Handle OAuth callback params ────────────────────────────────────────────
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const connected = params.get('social_connected');
    const error = params.get('social_error');

    if (connected) {
      const name = PLATFORMS.find(p => p.id === connected)?.label || connected;
      showToast(t.successMsg(name), true);
      loadStatus();
      // Clean URL without reload
      window.history.replaceState({}, '', window.location.pathname);
    } else if (error) {
      showToast(t.errorMsg(decodeURIComponent(error)), false);
      window.history.replaceState({}, '', window.location.pathname);
    }
  }, []);  // eslint-disable-line react-hooks/exhaustive-deps

  // ── Toast helper ────────────────────────────────────────────────────────────
  function showToast(msg, ok) {
    setToast({ msg, ok });
    setTimeout(() => setToast(null), 4000);
  }

  // ── Connect ─────────────────────────────────────────────────────────────────
  async function handleConnect(platformId) {
    setLoading(prev => ({ ...prev, [platformId]: true }));
    try {
      const res = await authFetch(`/api/social/connect/${platformId}`);
      const data = await res.json();
      if (data.url) {
        window.location.href = data.url;   // redirect to OAuth provider
      } else {
        showToast(t.errorMsg(data.error || 'Unknown error'), false);
      }
    } catch (e) {
      showToast(t.errorMsg(e.message), false);
    } finally {
      setLoading(prev => ({ ...prev, [platformId]: false }));
    }
  }

  // ── Disconnect ──────────────────────────────────────────────────────────────
  async function handleDisconnect(platformId) {
    setLoading(prev => ({ ...prev, [platformId]: true }));
    try {
      await authFetch(`/api/social/disconnect/${platformId}`, { method: 'DELETE' });
      setStatus(prev => {
        const next = { ...prev };
        delete next[platformId];
        return next;
      });
    } catch (e) {
      showToast(t.errorMsg(e.message), false);
    } finally {
      setLoading(prev => ({ ...prev, [platformId]: false }));
    }
  }

  // ── Render ──────────────────────────────────────────────────────────────────
  const connectedCount = Object.values(status).filter(s => s?.connected).length;

  return (
    <div style={{ marginBottom: 24, direction: t.dir }}>
      <h3 style={{ color: '#ccc', fontSize: 15, margin: '0 0 10px', fontWeight: 600 }}>
        {t.title}
      </h3>

      {/* Banner when no platforms are connected */}
      {connectedCount === 0 && (
        <div style={{
          background: '#1c1a08',
          border: '1px solid #ca8a04',
          borderRadius: 10,
          padding: '10px 14px',
          marginBottom: 12,
          color: '#fbbf24',
          fontSize: 13,
          lineHeight: 1.5,
        }}>
          {t.noPlatformsBanner}
        </div>
      )}

      <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
        {PLATFORMS.map(({ id, label, icon, color }) => {
          const info = status[id];
          const isConnected = info?.connected;
          const isExpired = info?.expired;
          const isLoading = loading[id];

          return (
            <div
              key={id}
              style={{
                background: '#12122a',
                border: `1px solid ${isConnected && !isExpired ? color : '#333'}`,
                borderRadius: 12,
                padding: '10px 14px',
                display: 'flex',
                alignItems: 'center',
                gap: 10,
                minWidth: 150,
              }}
            >
              <span style={{ fontSize: 22 }}>{icon}</span>
              <div style={{ flex: 1 }}>
                <div style={{ color: '#fff', fontSize: 13, fontWeight: 600 }}>{label}</div>
                <div style={{ fontSize: 11, color: isConnected ? (isExpired ? '#f59e0b' : '#4ade80') : '#666' }}>
                  {isConnected
                    ? (isExpired ? t.expired : (info?.pageName || t.connected))
                    : t.disconnected}
                </div>
              </div>
              <button
                onClick={() => isConnected ? handleDisconnect(id) : handleConnect(id)}
                disabled={isLoading}
                style={{
                  background: isConnected ? 'transparent' : color,
                  color: isConnected ? '#f87171' : '#fff',
                  border: isConnected ? '1px solid #f87171' : 'none',
                  borderRadius: 8,
                  padding: '5px 10px',
                  fontSize: 12,
                  cursor: isLoading ? 'not-allowed' : 'pointer',
                  opacity: isLoading ? 0.6 : 1,
                  whiteSpace: 'nowrap',
                }}
              >
                {isLoading ? t.connecting : (isConnected ? t.disconnect : t.connect)}
              </button>
            </div>
          );
        })}
      </div>

      {/* Toast notification */}
      {toast && (
        <div style={{
          marginTop: 12,
          padding: '10px 16px',
          borderRadius: 8,
          background: toast.ok ? '#14532d' : '#450a0a',
          border: `1px solid ${toast.ok ? '#4ade80' : '#f87171'}`,
          color: toast.ok ? '#4ade80' : '#f87171',
          fontSize: 13,
        }}>
          {toast.msg}
        </div>
      )}
    </div>
  );
}
