import { useState, useEffect } from 'react';

const API = '/api/advertising';

const PLATFORM_COLORS = {
  facebook: '#1877f2', instagram: '#e1306c', twitter: '#1da1f2',
  linkedin: '#0077b5', youtube: '#ff0000', tiktok: '#010101',
};
const PLATFORM_ICONS = {
  facebook: '📘', instagram: '📸', twitter: '🐦',
  linkedin: '💼', youtube: '▶️', tiktok: '🎵',
};

export default function AdvertisingDashboard() {
  const [sessionId] = useState(() => localStorage.getItem('adv_session_id') || '');
  const [profile, setProfile] = useState(null);
  const [scheduled, setScheduled] = useState(null);
  const [report, setReport] = useState(null);
  const [notifications, setNotifications] = useState([]);
  const [usage, setUsage] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');

  useEffect(() => {
    if (!sessionId) { setLoading(false); return; }
    Promise.all([
      fetch(`${API}/profile/${sessionId}`).then(r => r.json()).catch(() => null),
      fetch(`${API}/scheduled/${sessionId}`).then(r => r.json()).catch(() => null),
      fetch(`${API}/report/${sessionId}`).then(r => r.json()).catch(() => null),
      fetch(`${API}/notifications/${sessionId}`).then(r => r.json()).catch(() => null),
      fetch(`${API}/usage/${sessionId}`).then(r => r.json()).catch(() => null),
    ]).then(([p, s, r, n, u]) => {
      setProfile(p); setScheduled(s); setReport(r);
      setNotifications(n?.notifications || []);
      setUsage(u);
      setLoading(false);
    });
  }, [sessionId]);

  const markRead = async () => {
    await fetch(`${API}/notifications/${sessionId}/read`, { method: 'POST' });
    setNotifications([]);
  };

  const s = {
    page: { minHeight: '100vh', background: '#080812', color: 'white', padding: '24px', direction: 'rtl', fontFamily: '"Segoe UI", sans-serif' },
    header: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' },
    title: { margin: 0, fontSize: '28px', background: 'linear-gradient(135deg,#a78bfa,#60a5fa)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' },
    tabs: { display: 'flex', gap: '8px', marginBottom: '24px', borderBottom: '1px solid #1e1e3a', paddingBottom: '0' },
    tab: (active) => ({ padding: '10px 20px', cursor: 'pointer', border: 'none', background: 'none', color: active ? '#a78bfa' : '#6b7280', fontWeight: active ? 700 : 400, fontSize: '14px', borderBottom: active ? '2px solid #a78bfa' : '2px solid transparent', transition: 'all 0.2s' }),
    grid: { display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px', marginBottom: '24px' },
    card: { background: '#12122a', borderRadius: '12px', padding: '20px', border: '1px solid #1e1e3a' },
    cardTitle: { color: '#6b7280', fontSize: '12px', margin: '0 0 8px', textTransform: 'uppercase' },
    cardValue: { fontSize: '28px', fontWeight: 700, margin: '0 0 4px' },
    cardSub: { color: '#6b7280', fontSize: '12px', margin: 0 },
    section: { background: '#12122a', borderRadius: '12px', padding: '20px', marginBottom: '16px', border: '1px solid #1e1e3a' },
    sectionTitle: { margin: '0 0 16px', fontSize: '16px', fontWeight: 700 },
    badge: (type) => ({
      padding: '3px 10px', borderRadius: '12px', fontSize: '11px', fontWeight: 600,
      background: type === 'success' ? 'rgba(34,197,94,0.15)' : type === 'error' ? 'rgba(239,68,68,0.15)' : 'rgba(99,102,241,0.15)',
      color: type === 'success' ? '#4ade80' : type === 'error' ? '#f87171' : '#a78bfa',
    }),
    progressBar: (pct, color) => ({ height: '8px', borderRadius: '4px', background: '#1e1e3a', overflow: 'hidden', position: 'relative' }),
    progressFill: (pct, color) => ({ position: 'absolute', top: 0, right: 0, height: '100%', width: `${pct}%`, background: color || '#a78bfa', borderRadius: '4px', transition: 'width 0.5s' }),
  };

  if (loading) return <div style={{ ...s.page, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>טוען...</div>;

  if (!sessionId || !profile?.exists) return (
    <div style={{ ...s.page, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: '16px' }}>
      <span style={{ fontSize: '48px' }}>📊</span>
      <h2>אין נתונים עדיין</h2>
      <p style={{ color: '#6b7280' }}>התחל שיחה עם עוזר הפרסום כדי לראות את הדשבורד</p>
      <a href="/advertising" style={{ background: 'linear-gradient(135deg,#5b21b6,#1d4ed8)', color: 'white', padding: '10px 24px', borderRadius: '10px', textDecoration: 'none' }}>
        עבור לעוזר הפרסום
      </a>
    </div>
  );

  const exec = report?.executive_summary || {};
  const platforms = profile?.content_strategy?.preferred_platforms || [];

  return (
    <div style={s.page}>
      <div style={s.header}>
        <div>
          <h1 style={s.title}>📊 דשבורד פרסום</h1>
          <p style={{ color: '#6b7280', margin: '4px 0 0', fontSize: '14px' }}>{profile?.business_name || 'עסק שלי'} · {profile?.website_url}</p>
        </div>
        <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
          {notifications.length > 0 && (
            <button onClick={markRead} style={{ background: '#1e1e3a', border: '1px solid #4ade80', color: '#4ade80', borderRadius: '8px', padding: '6px 14px', cursor: 'pointer', fontSize: '13px' }}>
              🔔 {notifications.length} התראות חדשות
            </button>
          )}
          <a href="/advertising" style={{ background: 'linear-gradient(135deg,#5b21b6,#1d4ed8)', color: 'white', padding: '8px 16px', borderRadius: '8px', textDecoration: 'none', fontSize: '13px' }}>
            💬 לעוזר הפרסום
          </a>
        </div>
      </div>

      {/* Tabs */}
      <div style={s.tabs}>
        {[['overview', '📊 סקירה'], ['scheduled', '📅 מתוזמן'], ['notifications', '🔔 התראות'], ['usage', '⚡ שימוש']].map(([id, label]) => (
          <button key={id} style={s.tab(activeTab === id)} onClick={() => setActiveTab(id)}>{label}</button>
        ))}
      </div>

      {/* Overview Tab */}
      {activeTab === 'overview' && (
        <>
          <div style={s.grid}>
            <div style={s.card}>
              <p style={s.cardTitle}>ציון ביצועים</p>
              <p style={{ ...s.cardValue, color: exec.grade === 'A' ? '#4ade80' : exec.grade === 'B' ? '#fbbf24' : '#f87171' }}>
                {exec.performance_score || 0}
                <span style={{ fontSize: '16px', color: '#6b7280' }}>/100</span>
              </p>
              <p style={s.cardSub}>ציון {exec.grade || 'N/A'}</p>
            </div>
            <div style={s.card}>
              <p style={s.cardTitle}>פוסטים שפורסמו</p>
              <p style={s.cardValue}>{profile?.stats?.total_posts || 0}</p>
              <p style={s.cardSub}>סה"כ</p>
            </div>
            <div style={s.card}>
              <p style={s.cardTitle}>פוסטים מתוזמנים</p>
              <p style={{ ...s.cardValue, color: '#a78bfa' }}>{scheduled?.pending || 0}</p>
              <p style={s.cardSub}>ממתינים לפרסום</p>
            </div>
            <div style={s.card}>
              <p style={s.cardTitle}>פלטפורמות פעילות</p>
              <p style={s.cardValue}>{platforms.length || 0}</p>
              <p style={s.cardSub}>מתוך 6</p>
            </div>
          </div>

          {/* Platforms */}
          {platforms.length > 0 && (
            <div style={s.section}>
              <h3 style={s.sectionTitle}>🌐 פלטפורמות מחוברות</h3>
              <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
                {platforms.map(p => (
                  <div key={p} style={{ background: '#1e1e3a', borderRadius: '10px', padding: '12px 16px', display: 'flex', alignItems: 'center', gap: '8px', border: `1px solid ${PLATFORM_COLORS[p] || '#3f3f6e'}` }}>
                    <span style={{ fontSize: '20px' }}>{PLATFORM_ICONS[p] || '🌐'}</span>
                    <span style={{ fontSize: '14px', fontWeight: 600 }}>{p}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Next week plan */}
          {report?.next_week_plan && (
            <div style={s.section}>
              <h3 style={s.sectionTitle}>📅 תכנית שבוע הבא</h3>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                <div>
                  <p style={{ color: '#6b7280', fontSize: '13px', margin: '0 0 8px' }}>סוגי תוכן מומלצים:</p>
                  {(report.next_week_plan.content_themes || []).map((t, i) => (
                    <div key={i} style={{ background: '#1e1e3a', borderRadius: '8px', padding: '8px 12px', marginBottom: '6px', fontSize: '13px' }}>{t}</div>
                  ))}
                </div>
                <div>
                  <p style={{ color: '#6b7280', fontSize: '13px', margin: '0 0 8px' }}>פעולות נדרשות:</p>
                  {(report.action_items || []).map((item, i) => (
                    <div key={i} style={{ fontSize: '13px', padding: '4px 0', color: '#c4b5fd' }}>{item}</div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </>
      )}

      {/* Scheduled Tab */}
      {activeTab === 'scheduled' && (
        <div style={s.section}>
          <h3 style={s.sectionTitle}>📅 פוסטים מתוזמנים ({scheduled?.pending || 0} ממתינים)</h3>
          {(scheduled?.jobs || []).length === 0 ? (
            <p style={{ color: '#6b7280', textAlign: 'center', padding: '32px' }}>אין פוסטים מתוזמנים. בקש מהעוזר לתזמן פוסטים!</p>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              {(scheduled.jobs || []).map(job => (
                <div key={job.job_id} style={{ background: '#1e1e3a', borderRadius: '10px', padding: '14px 16px', display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <div style={{ flex: 1 }}>
                    <div style={{ display: 'flex', gap: '8px', marginBottom: '6px' }}>
                      {(job.platforms || []).map(p => (
                        <span key={p} style={{ fontSize: '16px' }}>{PLATFORM_ICONS[p] || '🌐'}</span>
                      ))}
                      <span style={s.badge(job.status === 'published' ? 'success' : job.status === 'failed' ? 'error' : 'info')}>
                        {job.status === 'published' ? '✅ פורסם' : job.status === 'failed' ? '❌ נכשל' : '⏳ ממתין'}
                      </span>
                    </div>
                    <p style={{ margin: '0 0 4px', fontSize: '13px', color: '#e2e8f0' }}>{job.content?.slice(0, 100)}...</p>
                    <p style={{ margin: 0, fontSize: '11px', color: '#6b7280' }}>
                      {new Date(job.scheduled_for).toLocaleString('he-IL')}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Notifications Tab */}
      {activeTab === 'notifications' && (
        <div style={s.section}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
            <h3 style={{ margin: 0, fontSize: '16px', fontWeight: 700 }}>🔔 התראות</h3>
            {notifications.length > 0 && (
              <button onClick={markRead} style={{ background: 'none', border: '1px solid #3f3f6e', color: '#a78bfa', borderRadius: '8px', padding: '4px 12px', cursor: 'pointer', fontSize: '12px' }}>סמן הכל כנקרא</button>
            )}
          </div>
          {notifications.length === 0 ? (
            <p style={{ color: '#6b7280', textAlign: 'center', padding: '32px' }}>אין התראות חדשות</p>
          ) : (
            notifications.map(n => (
              <div key={n.id} style={{ background: '#1e1e3a', borderRadius: '10px', padding: '12px 16px', marginBottom: '8px', borderRight: `3px solid ${n.type === 'success' ? '#4ade80' : n.type === 'error' ? '#f87171' : '#a78bfa'}` }}>
                <p style={{ margin: '0 0 4px', fontWeight: 600, fontSize: '14px' }}>{n.title}</p>
                <p style={{ margin: '0 0 4px', fontSize: '13px', color: '#c4b5fd' }}>{n.message}</p>
                <p style={{ margin: 0, fontSize: '11px', color: '#6b7280' }}>{new Date(n.created_at).toLocaleString('he-IL')}</p>
              </div>
            ))
          )}
        </div>
      )}

      {/* Usage Tab */}
      {activeTab === 'usage' && usage && (
        <div style={s.section}>
          <h3 style={s.sectionTitle}>⚡ שימוש ב-API</h3>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
            {[['שעה אחרונה', usage.hourly], ['יום אחרון', usage.daily]].map(([label, data]) => (
              <div key={label} style={{ background: '#1e1e3a', borderRadius: '10px', padding: '16px' }}>
                <p style={{ margin: '0 0 8px', color: '#6b7280', fontSize: '13px' }}>{label}</p>
                <p style={{ margin: '0 0 10px', fontSize: '22px', fontWeight: 700 }}>
                  {data?.used || 0} <span style={{ fontSize: '14px', color: '#6b7280' }}>/ {data?.limit}</span>
                </p>
                <div style={s.progressBar()}>
                  <div style={s.progressFill(((data?.used || 0) / (data?.limit || 1)) * 100, data?.used > data?.limit * 0.8 ? '#f87171' : '#a78bfa')} />
                </div>
                <p style={{ margin: '6px 0 0', fontSize: '12px', color: '#6b7280' }}>{data?.remaining} הודעות נותרו</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
