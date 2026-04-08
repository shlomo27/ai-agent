import { useState, useRef, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';

const API_BASE = '/api/advertising';

const QUICK_ACTIONS = [
  { label: '🚀 התחל פרסום', msg: 'אני רוצה להתחיל לפרסם את העסק שלי ברשתות החברתיות' },
  { label: '📊 ניתוח ביצועים', msg: 'תראה לי ניתוח ביצועים של הפרסום שלי' },
  { label: '📅 לוח תוכן', msg: 'צור לי לוח תוכן לחודש הקרוב' },
  { label: '🎯 קמפיין ממומן', msg: 'אני רוצה להקים קמפיין פרסום ממומן' },
  { label: '💡 המלצות', msg: 'מה הפלטפורמות הטובות ביותר בשבילי?' },
  { label: '✍️ צור פוסט', msg: 'עזור לי לכתוב פוסט מושלם לרשתות החברתיות' },
];

const PLAN_LABELS = {
  free:            { label: 'Free',            color: '#6b7280' },
  basic:           { label: 'Basic',           color: '#3b82f6' },
  pro:             { label: 'Pro',             color: '#8b5cf6' },
  business:        { label: 'Business',        color: '#f59e0b' },
  bundle_starter:  { label: 'Bundle Starter',  color: '#3b82f6' },
  bundle_pro:      { label: 'Bundle Pro',      color: '#8b5cf6' },
  bundle_business: { label: 'Bundle Business', color: '#f59e0b' },
};

export default function AdvertisingAgent() {
  const { token, user } = useAuth();
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [onboardingComplete, setOnboardingComplete] = useState(false);
  const [businessName, setBusinessName] = useState('');
  const [plan, setPlan] = useState('free');
  const messagesEndRef = useRef(null);

  // Authenticated fetch helper
  const authFetch = (url, opts = {}) =>
    fetch(url, {
      ...opts,
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
        ...(opts.headers || {}),
      },
    });

  // Load profile + plan on mount
  useEffect(() => {
    if (!token) return;

    authFetch(`${API_BASE}/profile`)
      .then(r => r.json())
      .then(data => {
        if (data.onboarding_complete) {
          setOnboardingComplete(true);
          setBusinessName(data.business_name || '');
        }
      })
      .catch(() => {});

    authFetch(`${API_BASE}/plan`)
      .then(r => r.json())
      .then(data => { if (data.plan) setPlan(data.plan); })
      .catch(() => {});

    setMessages([{
      role: 'assistant',
      content: `שלום ${user?.name ? user.name : ''}! אני עוזר הפרסום החכם שלך 🚀\n\nאני פועל על בסיס Claude AI ויכול לעזור לך לפרסם בכל הרשתות החברתיות באופן חכם וממוקד.\n\nאם זו הפעם הראשונה שלנו - אשאל אותך כמה שאלות כדי להכיר את העסק שלך.\n\nמה תרצה לעשות?`,
    }]);
  }, [token]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const sendMessage = async (text) => {
    const msgText = text || input;
    if (!msgText.trim() || loading) return;

    setMessages(prev => [...prev, { role: 'user', content: msgText }]);
    setInput('');
    setLoading(true);

    try {
      const res = await authFetch(`${API_BASE}/chat`, {
        method: 'POST',
        body: JSON.stringify({ message: msgText }),
      });

      if (res.status === 429) {
        const data = await res.json();
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: `⚠️ ${data.detail || 'הגעת למגבלת ההודעות. שדרג תוכנית לקבלת יותר הודעות.'}`,
        }]);
        return;
      }

      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();

      setMessages(prev => [...prev, {
        role: 'assistant',
        content: data.response || 'לא התקבלה תשובה',
      }]);

      if (data.onboarding_complete) {
        setOnboardingComplete(true);
        if (data.business_name) setBusinessName(data.business_name);
      }
    } catch (err) {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: `❌ שגיאה בחיבור לעוזר. נסה שוב.\n(${err.message})`,
      }]);
    } finally {
      setLoading(false);
    }
  };

  const resetProfile = async () => {
    if (!confirm('האם לאפס את פרופיל העסק ולהתחיל מחדש?')) return;
    await authFetch(`${API_BASE}/profile`, { method: 'DELETE' });
    setOnboardingComplete(false);
    setBusinessName('');
    setMessages([{
      role: 'assistant',
      content: 'הפרופיל אופס. בוא נתחיל מחדש! ספר לי על העסק שלך.',
    }]);
  };

  const planInfo = PLAN_LABELS[plan] || PLAN_LABELS.free;

  const s = {
    wrap: {
      display: 'flex', flexDirection: 'column', height: '100%',
      background: '#0a0a14', fontFamily: '"Segoe UI", Arial, sans-serif', direction: 'rtl',
      borderRadius: '16px', overflow: 'hidden',
    },
    header: {
      display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      padding: '16px 20px', background: 'linear-gradient(135deg, #5b21b6, #1d4ed8)',
      color: 'white', flexShrink: 0,
    },
    headerLeft: { display: 'flex', alignItems: 'center', gap: '12px' },
    headerInfo: { display: 'flex', flexDirection: 'column' },
    headerTitle: { margin: 0, fontSize: '18px', fontWeight: 700 },
    headerSub: { margin: 0, fontSize: '12px', opacity: 0.8 },
    statusBadge: {
      background: onboardingComplete ? 'rgba(34,197,94,0.2)' : 'rgba(251,191,36,0.2)',
      color: onboardingComplete ? '#4ade80' : '#fbbf24',
      border: `1px solid ${onboardingComplete ? '#4ade80' : '#fbbf24'}`,
      borderRadius: '20px', padding: '3px 10px', fontSize: '11px', fontWeight: 600,
    },
    planBadge: {
      background: `${planInfo.color}22`,
      color: planInfo.color,
      border: `1px solid ${planInfo.color}`,
      borderRadius: '20px', padding: '3px 10px', fontSize: '11px', fontWeight: 600,
    },
    resetBtn: {
      background: 'rgba(255,255,255,0.1)', border: 'none', color: 'white',
      borderRadius: '8px', padding: '4px 10px', cursor: 'pointer', fontSize: '11px',
    },
    quickActions: {
      display: 'flex', gap: '8px', padding: '10px 14px', flexWrap: 'wrap',
      background: '#12122a', flexShrink: 0, borderBottom: '1px solid #1e1e3a',
    },
    qBtn: {
      background: '#1e1e3a', border: '1px solid #2d2d5e', color: '#a5b4fc',
      padding: '5px 12px', borderRadius: '16px', cursor: 'pointer',
      fontSize: '12px', whiteSpace: 'nowrap', transition: 'all 0.15s',
    },
    messages: {
      flex: 1, overflowY: 'auto', padding: '16px 14px',
      display: 'flex', flexDirection: 'column', gap: '12px',
    },
    userBubble: {
      alignSelf: 'flex-start', background: '#1e1e3a', color: '#e2e8f0',
      padding: '10px 14px', borderRadius: '16px 16px 4px 16px',
      maxWidth: '78%', lineHeight: 1.6, fontSize: '14px',
    },
    aiBubble: {
      alignSelf: 'flex-end', background: 'linear-gradient(135deg, #5b21b6, #1d4ed8)',
      color: 'white', padding: '10px 14px', borderRadius: '16px 16px 16px 4px',
      maxWidth: '85%', lineHeight: 1.6, fontSize: '14px', whiteSpace: 'pre-wrap',
    },
    loadingBubble: {
      alignSelf: 'flex-end', background: '#1e1e3a',
      padding: '12px 18px', borderRadius: '16px',
      display: 'flex', gap: '5px', alignItems: 'center',
    },
    dot: {
      width: '7px', height: '7px', borderRadius: '50%',
      background: '#a5b4fc', animation: 'bounce 1.2s infinite',
    },
    inputArea: {
      display: 'flex', gap: '8px', padding: '12px 14px',
      background: '#12122a', borderTop: '1px solid #1e1e3a', flexShrink: 0,
    },
    textarea: {
      flex: 1, background: '#1e1e3a', border: '1px solid #2d2d5e', color: '#e2e8f0',
      borderRadius: '10px', padding: '10px 13px', fontSize: '14px',
      resize: 'none', direction: 'rtl', outline: 'none', fontFamily: 'inherit',
      lineHeight: 1.5,
    },
    sendBtn: {
      background: 'linear-gradient(135deg, #5b21b6, #1d4ed8)', color: 'white',
      border: 'none', borderRadius: '10px', padding: '10px 18px',
      cursor: 'pointer', fontWeight: 700, fontSize: '14px', flexShrink: 0,
    },
  };

  return (
    <div style={s.wrap}>
      <style>{`
        @keyframes bounce {
          0%,80%,100% { transform:scale(0.7); opacity:0.4; }
          40% { transform:scale(1.1); opacity:1; }
        }
        .qbtn:hover { background:#2d2d5e !important; color:white !important; }
        .sbtn:hover { opacity:0.85; }
        .msg-table { width:100%; border-collapse:collapse; margin:8px 0; }
        .msg-table th { background:rgba(255,255,255,0.15); padding:6px 10px; text-align:right; font-size:12px; }
        .msg-table td { padding:6px 10px; font-size:13px; border-top:1px solid rgba(255,255,255,0.08); }
      `}</style>

      {/* Header */}
      <div style={s.header}>
        <div style={s.headerLeft}>
          <span style={{ fontSize: '28px' }}>🚀</span>
          <div style={s.headerInfo}>
            <h2 style={s.headerTitle}>
              עוזר פרסום חכם {businessName ? `| ${businessName}` : ''}
            </h2>
            <p style={s.headerSub}>מופעל על ידי Claude AI · claude-opus-4-6</p>
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
          <span style={s.planBadge}>{planInfo.label}</span>
          <span style={s.statusBadge}>
            {onboardingComplete ? '✅ פרופיל מוכן' : '⚙️ הגדרה ראשונית'}
          </span>
          {onboardingComplete && (
            <button style={s.resetBtn} onClick={resetProfile}>איפוס</button>
          )}
        </div>
      </div>

      {/* Quick Actions */}
      <div style={s.quickActions}>
        {QUICK_ACTIONS.map(a => (
          <button
            key={a.label}
            className="qbtn"
            style={s.qBtn}
            onClick={() => sendMessage(a.msg)}
            disabled={loading}
          >
            {a.label}
          </button>
        ))}
      </div>

      {/* Messages */}
      <div style={s.messages}>
        {messages.map((msg, i) => (
          <div key={i} style={msg.role === 'user' ? s.userBubble : s.aiBubble}>
            {msg.content}
          </div>
        ))}
        {loading && (
          <div style={s.loadingBubble}>
            {[0, 0.2, 0.4].map((delay, i) => (
              <span key={i} style={{ ...s.dot, animationDelay: `${delay}s` }} />
            ))}
            <span style={{ color: '#a5b4fc', fontSize: '12px', marginRight: '6px' }}>
              Claude חושב...
            </span>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div style={s.inputArea}>
        <textarea
          style={s.textarea}
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault();
              sendMessage();
            }
          }}
          placeholder="כתוב הודעה... (Enter לשליחה, Shift+Enter לשורה חדשה)"
          rows={2}
          disabled={loading}
        />
        <button
          className="sbtn"
          style={{ ...s.sendBtn, opacity: loading || !input.trim() ? 0.4 : 1 }}
          onClick={() => sendMessage()}
          disabled={loading || !input.trim()}
        >
          שלח ➤
        </button>
      </div>
    </div>
  );
}
