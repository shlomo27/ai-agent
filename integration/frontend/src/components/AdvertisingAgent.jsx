import { useState, useRef, useEffect } from 'react';
import './AdvertisingAgent.css';

const API_BASE = '/api/advertising';

export default function AdvertisingAgent() {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: 'שלום! אני עוזר הפרסום החכם שלך 🚀\n\nאני יכול לעזור לך:\n• לפרסם תוכן ברשתות חברתיות\n• ליצור קמפיינים פרסומיים\n• לנתח את הביצועים שלך\n• להמליץ על פלטפורמות חדשות\n\nמה תרצה לעשות היום?',
    },
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [sessionId] = useState(() => `session_${Date.now()}`);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const sendMessage = async () => {
    if (!input.trim() || loading) return;

    const userMessage = { role: 'user', content: input };
    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const res = await fetch(`${API_BASE}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: input, session_id: sessionId }),
      });
      const data = await res.json();
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: data.response || 'שגיאה בקבלת תשובה' },
      ]);
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: '❌ שגיאה בחיבור לעוזר. נסה שוב.' },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const quickActions = [
    { label: '📊 ניתוח ביצועים', msg: 'תראה לי את ניתוח הביצועים שלי' },
    { label: '✍️ צור פוסט', msg: 'עזור לי ליצור פוסט לרשתות חברתיות' },
    { label: '🎯 קמפיין חדש', msg: 'אני רוצה ליצור קמפיין פרסום חדש' },
    { label: '💡 המלצות', msg: 'מה הפלטפורמות הטובות ביותר בשבילי?' },
  ];

  return (
    <div className="adv-agent">
      <div className="adv-header">
        <div className="adv-header-icon">🚀</div>
        <div>
          <h2>עוזר פרסום חכם</h2>
          <p>מופעל על ידי Claude AI</p>
        </div>
      </div>

      <div className="adv-quick-actions">
        {quickActions.map((action) => (
          <button
            key={action.label}
            className="adv-quick-btn"
            onClick={() => { setInput(action.msg); }}
          >
            {action.label}
          </button>
        ))}
      </div>

      <div className="adv-messages">
        {messages.map((msg, i) => (
          <div key={i} className={`adv-message adv-message--${msg.role}`}>
            <div className="adv-bubble">
              {msg.content.split('\n').map((line, j) => (
                <span key={j}>{line}<br /></span>
              ))}
            </div>
          </div>
        ))}
        {loading && (
          <div className="adv-message adv-message--assistant">
            <div className="adv-bubble adv-bubble--loading">
              <span></span><span></span><span></span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="adv-input-area">
        <textarea
          className="adv-input"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="כתוב הודעה... (Enter לשליחה)"
          rows={2}
          disabled={loading}
        />
        <button
          className="adv-send-btn"
          onClick={sendMessage}
          disabled={loading || !input.trim()}
        >
          שלח ➤
        </button>
      </div>
    </div>
  );
}
