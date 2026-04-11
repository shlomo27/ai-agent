import { useState, useRef, useEffect, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';

const API_BASE = '/api/advertising';

const QUICK_ACTIONS = {
  he: [
    { label: '🚀 התחל פרסום', msg: 'אני רוצה להתחיל לפרסם את העסק שלי ברשתות החברתיות' },
    { label: '📊 ניתוח ביצועים', msg: 'תראה לי ניתוח ביצועים של הפרסום שלי' },
    { label: '📅 לוח תוכן', msg: 'צור לי לוח תוכן לחודש הקרוב' },
    { label: '🎯 קמפיין ממומן', msg: 'אני רוצה להקים קמפיין פרסום ממומן' },
    { label: '💡 המלצות', msg: 'מה הפלטפורמות הטובות ביותר בשבילי?' },
    { label: '✍️ צור פוסט', msg: 'עזור לי לכתוב פוסט מושלם לרשתות החברתיות' },
  ],
  en: [
    { label: '🚀 Start Publishing', msg: 'I want to start publishing my business on social media' },
    { label: '📊 Performance Analysis', msg: 'Show me my advertising performance analysis' },
    { label: '📅 Content Calendar', msg: 'Create a content calendar for next month' },
    { label: '🎯 Paid Campaign', msg: 'I want to set up a paid advertising campaign' },
    { label: '💡 Recommendations', msg: 'What are the best platforms for my business?' },
    { label: '✍️ Create Post', msg: 'Help me write a perfect social media post' },
  ],
};

const UI_TEXT = {
  he: {
    headerTitle: 'עוזר פרסום חכם',
    subtitle: 'מופעל על ידי Claude AI · claude-opus-4-6',
    profileReady: '✅ פרופיל מוכן',
    setupFirst: '⚙️ הגדרה ראשונית',
    reset: 'איפוס',
    thinking: 'Claude חושב...',
    placeholder: 'כתוב הודעה... (Enter לשליחה, Shift+Enter לשורה חדשה)',
    send: 'שלח ➤',
    error: '❌ שגיאה בחיבור לעוזר. נסה שוב.',
    noResponse: 'לא התקבלה תשובה',
    rateLimited: 'הגעת למגבלת ההודעות. שדרג תוכנית לקבלת יותר הודעות.',
    welcomeNew: (name) =>
      `שלום${name}! 👋 אני **מפרסם** - עוזר הפרסום החכם של ilmariai.com.\n\nאני רואה שזו הפעם הראשונה שלנו ביחד - מעולה! 🎉\n\nכדי שאוכל לעבוד בצורה חכמה ומדויקת, אצטרך להכיר קצת את העסק שלך.\n\n**האם אתה מוכן להתחיל את תהליך ההכרות?**`,
    resetConfirm: 'האם לאפס את פרופיל העסק ולהתחיל מחדש?',
    resetMsg: 'הפרופיל אופס. בוא נתחיל מחדש! ספר לי על העסק שלך.',
    dir: 'rtl',
    langBtn: '🇺🇸 EN',
  },
  en: {
    headerTitle: 'Smart Advertising Assistant',
    subtitle: 'Powered by Claude AI · claude-opus-4-6',
    profileReady: '✅ Profile Ready',
    setupFirst: '⚙️ Initial Setup',
    reset: 'Reset',
    thinking: 'Claude thinking...',
    placeholder: 'Type a message... (Enter to send, Shift+Enter for new line)',
    send: 'Send ➤',
    error: '❌ Connection error. Please try again.',
    noResponse: 'No response received',
    rateLimited: 'Message limit reached. Upgrade your plan for more messages.',
    welcomeNew: (name) =>
      `Hello${name}! 👋 I'm **Mefaresem** — the smart advertising assistant of ilmariai.com.\n\nI can see this is our first time together — great! 🎉\n\nTo work smartly and accurately, I'll need to get to know your business a little.\n\n**Are you ready to start the onboarding process?**`,
    resetConfirm: 'Reset the business profile and start over?',
    resetMsg: "Profile reset. Let's start fresh! Tell me about your business.",
    dir: 'ltr',
    langBtn: '🇮🇱 עב',
  },
};

const PLAN_LABELS = {
  free:            { label: 'Free',            color: '#6b7280' },
  basic:           { label: 'Basic',           color: '#3b82f6' },
  pro:             { label: 'Pro',             color: '#8b5cf6' },
  business:        { label: 'Business',        color: '#f59e0b' },
  bundle_starter:  { label: 'Bundle Starter',  color: '#3b82f6' },
  bundle_pro:      { label: 'Bundle Pro',      color: '#8b5cf6' },
  bundle_business: { label: 'Bundle Business', color: '#f59e0b' },
};

// Detect if a message is still the auto-generated welcome (no real conversation yet)
function isOnlyWelcome(msgs) {
  return msgs.length === 1 && msgs[0].role === 'assistant';
}

export default function AdvertisingAgent({ language: langProp, onLanguageChange }) {
  const { token, user } = useAuth();

  // Language: controlled by parent if langProp is provided, otherwise self-managed
  const [langInternal, setLangInternal] = useState(
    () => localStorage.getItem('adv_lang') || 'he'
  );
  const language = langProp !== undefined ? langProp : langInternal;

  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [onboardingComplete, setOnboardingComplete] = useState(false);
  const [businessName, setBusinessName] = useState('');
  const [plan, setPlan] = useState('free');
  // Track whether history came from server (real conversation) vs just welcome
  const [hasRealHistory, setHasRealHistory] = useState(false);
  const messagesEndRef = useRef(null);
  const userNameRef = useRef('');

  const t = UI_TEXT[language] || UI_TEXT.he;

  const authFetch = useCallback((url, opts = {}) =>
    fetch(url, {
      ...opts,
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
        ...(opts.headers || {}),
      },
    }), [token]);

  // Load profile, plan and history on mount
  useEffect(() => {
    if (!token) return;
    Promise.all([
      authFetch(`${API_BASE}/profile`).then(r => r.json()).catch(() => ({})),
      authFetch(`${API_BASE}/plan`).then(r => r.json()).catch(() => ({})),
      authFetch(`${API_BASE}/chat/history`).then(r => r.json()).catch(() => ({ history: [] })),
    ]).then(([profileData, planData, historyData]) => {
      if (profileData.onboarding_complete) {
        setOnboardingComplete(true);
        setBusinessName(profileData.business_name || '');
      }
      if (planData.plan) setPlan(planData.plan);

      const history = (historyData.history || [])
        .map(m => ({ role: m.role, content: typeof m.content === 'string' ? m.content : '' }))
        .filter(m => m.content);

      const name = user?.name ? ` ${user.name}` : '';
      userNameRef.current = name;

      if (history.length > 0) {
        setMessages(history);
        setHasRealHistory(true);
      } else {
        setMessages([{ role: 'assistant', content: t.welcomeNew(name) }]);
        setHasRealHistory(false);
      }
    });
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  // When language changes, update welcome message ONLY if no real conversation started yet
  useEffect(() => {
    setMessages(prev => {
      if (isOnlyWelcome(prev) && !hasRealHistory) {
        return [{ role: 'assistant', content: (UI_TEXT[language] || UI_TEXT.he).welcomeNew(userNameRef.current) }];
      }
      return prev;
    });
  }, [language, hasRealHistory]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const sendMessage = async (text) => {
    const msgText = text || input;
    if (!msgText.trim() || loading) return;

    setMessages(prev => [...prev, { role: 'user', content: msgText }]);
    setHasRealHistory(true);
    setInput('');
    setLoading(true);

    try {
      const res = await authFetch(`${API_BASE}/chat`, {
        method: 'POST',
        body: JSON.stringify({ message: msgText, language }),
      });

      if (res.status === 429) {
        const data = await res.json();
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: `⚠️ ${data.detail || t.rateLimited}`,
        }]);
        return;
      }

      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();

      setMessages(prev => [...prev, {
        role: 'assistant',
        content: data.response || t.noResponse,
      }]);

      if (data.onboarding_complete) {
        setOnboardingComplete(true);
        if (data.business_name) setBusinessName(data.business_name);
      }
    } catch (err) {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: `${t.error}\n(${err.message})`,
      }]);
    } finally {
      setLoading(false);
    }
  };

  const toggleLanguage = () => {
    const next = language === 'he' ? 'en' : 'he';
    // 1. Update internal state (self-managed mode)
    setLangInternal(next);
    // 2. Persist to localStorage
    localStorage.setItem('adv_lang', next);
    // 3. Notify parent via prop (controlled mode)
    if (onLanguageChange) onLanguageChange(next);
    // 4. Fire custom event so AdvertisingPage title can update even without prop wiring
    window.dispatchEvent(new CustomEvent('adv_lang_change', { detail: next }));
  };

  const resetProfile = async () => {
    if (!confirm(t.resetConfirm)) return;
    await authFetch(`${API_BASE}/profile`, { method: 'DELETE' });
    setOnboardingComplete(false);
    setBusinessName('');
    setHasRealHistory(false);
    setMessages([{ role: 'assistant', content: t.resetMsg }]);
  };

  const planInfo = PLAN_LABELS[plan] || PLAN_LABELS.free;

  const s = {
    wrap: {
      display: 'flex', flexDirection: 'column', height: '100%',
      background: '#0a0a14', fontFamily: '"Segoe UI", Arial, sans-serif',
      direction: t.dir, borderRadius: '16px', overflow: 'hidden',
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
      background: `${planInfo.color}22`, color: planInfo.color,
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
      alignSelf: language === 'he' ? 'flex-start' : 'flex-end',
      background: '#1e1e3a', color: '#e2e8f0',
      padding: '10px 14px', borderRadius: '16px 16px 4px 16px',
      maxWidth: '78%', lineHeight: 1.6, fontSize: '14px',
    },
    aiBubble: {
      alignSelf: language === 'he' ? 'flex-end' : 'flex-start',
      background: 'linear-gradient(135deg, #5b21b6, #1d4ed8)',
      color: 'white', padding: '10px 14px', borderRadius: '16px 16px 16px 4px',
      maxWidth: '85%', lineHeight: 1.6, fontSize: '14px', whiteSpace: 'pre-wrap',
    },
    loadingBubble: {
      alignSelf: language === 'he' ? 'flex-end' : 'flex-start',
      background: '#1e1e3a', padding: '12px 18px', borderRadius: '16px',
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
      resize: 'none', direction: t.dir, outline: 'none', fontFamily: 'inherit',
      lineHeight: 1.5,
    },
    langToggle: {
      background: 'rgba(255,255,255,0.15)', border: '1px solid rgba(255,255,255,0.3)',
      color: 'white', borderRadius: '8px', padding: '4px 10px',
      cursor: 'pointer', fontSize: '12px', fontWeight: 600,
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
              {t.headerTitle}{businessName ? ` | ${businessName}` : ''}
            </h2>
            <p style={s.headerSub}>{t.subtitle}</p>
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
          <button style={s.langToggle} onClick={toggleLanguage}>
            {t.langBtn}
          </button>
          <span style={s.planBadge}>{planInfo.label}</span>
          <span style={s.statusBadge}>
            {onboardingComplete ? t.profileReady : t.setupFirst}
          </span>
          {onboardingComplete && (
            <button style={s.resetBtn} onClick={resetProfile}>{t.reset}</button>
          )}
        </div>
      </div>

      {/* Quick Actions */}
      <div style={s.quickActions}>
        {(QUICK_ACTIONS[language] || QUICK_ACTIONS.he).map(a => (
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
            <span style={{ color: '#a5b4fc', fontSize: '12px', marginInlineStart: '6px' }}>
              {t.thinking}
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
          placeholder={t.placeholder}
          rows={2}
          disabled={loading}
        />
        <button
          className="sbtn"
          style={{ ...s.sendBtn, opacity: loading || !input.trim() ? 0.4 : 1 }}
          onClick={() => sendMessage()}
          disabled={loading || !input.trim()}
        >
          {t.send}
        </button>
      </div>
    </div>
  );
}
