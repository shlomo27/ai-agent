import { useState, useEffect } from 'react';
import AdvertisingAgent from '../components/AdvertisingAgent';
import './AdvertisingPage.css';

const PAGE_TEXT = {
  he: {
    title: '🚀 עוזר פרסום חכם',
    subtitle: 'פרסם ברשתות חברתיות, צור קמפיינים ונתח ביצועים — הכל בעזרת AI',
    dir: 'rtl',
  },
  en: {
    title: '🚀 Smart Advertising Assistant',
    subtitle: 'Publish on social media, create campaigns & analyze performance — all with AI',
    dir: 'ltr',
  },
};

export default function AdvertisingPage() {
  // Initialize from localStorage — same key used by AdvertisingAgent
  const [lang, setLang] = useState(() => localStorage.getItem('adv_lang') || 'he');

  useEffect(() => {
    // Listen for the custom event fired by AdvertisingAgent on every toggle
    const handler = (e) => setLang(e.detail || 'he');
    window.addEventListener('adv_lang_change', handler);
    return () => window.removeEventListener('adv_lang_change', handler);
  }, []);

  // Also called via prop — redundant with the event but keeps things in sync
  const handleLangChange = (newLang) => setLang(newLang);

  const t = PAGE_TEXT[lang] || PAGE_TEXT.he;

  return (
    <div className="adv-page" dir={t.dir}>
      <div className="adv-page-header">
        <h1>{t.title}</h1>
        <p>{t.subtitle}</p>
      </div>
      <div className="adv-page-content">
        <AdvertisingAgent language={lang} onLanguageChange={handleLangChange} />
      </div>
    </div>
  );
}
