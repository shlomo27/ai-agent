/**
 * AdvertisingNavCard — a card/button to place anywhere in the app
 * (Dashboard, LandingPage, sidebar, etc.) that navigates to /advertising.
 *
 * Usage:
 *   import AdvertisingNavCard from '../components/AdvertisingNavCard';
 *   <AdvertisingNavCard />
 *
 * The card auto-detects language from localStorage key 'adv_lang'.
 */
import { useNavigate } from 'react-router-dom';
import { useState } from 'react';

const TEXT = {
  he: {
    badge: 'חדש',
    title: '🚀 עוזר פרסום AI',
    desc: 'פרסם ברשתות חברתיות אוטומטית עם בינה מלאכותית',
    features: ['פייסבוק • אינסטגרם • לינקדאין', 'יצירת תוכן חכמה', 'קמפיינים ממומנים'],
    cta: 'התחל לפרסם ←',
    dir: 'rtl',
  },
  en: {
    badge: 'New',
    title: '🚀 AI Advertising Agent',
    desc: 'Automatically publish on social media with AI',
    features: ['Facebook • Instagram • LinkedIn', 'Smart content creation', 'Paid campaigns'],
    cta: '→ Start Publishing',
    dir: 'ltr',
  },
};

export default function AdvertisingNavCard({ style }) {
  const navigate = useNavigate();
  const lang = localStorage.getItem('adv_lang') || 'he';
  const t = TEXT[lang] || TEXT.he;
  const [hover, setHover] = useState(false);

  return (
    <div
      dir={t.dir}
      onClick={() => navigate('/advertising')}
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
      style={{
        background: hover
          ? 'linear-gradient(135deg, #4c1d95, #1e3a8a)'
          : 'linear-gradient(135deg, #3b0764, #1e3a8a)',
        border: '1px solid rgba(139,92,246,0.4)',
        borderRadius: 16,
        padding: '20px 24px',
        cursor: 'pointer',
        transition: 'all 0.2s',
        transform: hover ? 'translateY(-2px)' : 'none',
        boxShadow: hover ? '0 8px 30px rgba(91,33,182,0.4)' : '0 2px 12px rgba(0,0,0,0.3)',
        color: 'white',
        userSelect: 'none',
        ...(style || {}),
      }}
    >
      {/* Badge */}
      <span style={{
        background: '#7c3aed', color: 'white', fontSize: 10, fontWeight: 700,
        borderRadius: 20, padding: '2px 8px', marginBottom: 10, display: 'inline-block',
        letterSpacing: '0.5px', textTransform: 'uppercase',
      }}>
        {t.badge}
      </span>

      <div style={{ fontSize: 20, fontWeight: 800, margin: '6px 0 4px' }}>
        {t.title}
      </div>

      <div style={{ fontSize: 13, color: 'rgba(255,255,255,0.75)', marginBottom: 14, lineHeight: 1.4 }}>
        {t.desc}
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 4, marginBottom: 18 }}>
        {t.features.map((f, i) => (
          <div key={i} style={{ fontSize: 12, color: 'rgba(255,255,255,0.6)', display: 'flex', gap: 6, alignItems: 'center' }}>
            <span style={{ color: '#a78bfa' }}>✓</span> {f}
          </div>
        ))}
      </div>

      <div style={{
        background: 'rgba(255,255,255,0.12)', borderRadius: 10,
        padding: '8px 16px', textAlign: 'center', fontSize: 13,
        fontWeight: 700, color: 'white', border: '1px solid rgba(255,255,255,0.2)',
      }}>
        {t.cta}
      </div>
    </div>
  );
}
