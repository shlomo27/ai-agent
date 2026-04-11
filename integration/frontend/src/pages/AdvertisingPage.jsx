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
  const [lang, setLang] = useState(() => localStorage.getItem('adv_lang') || 'he');

  // Listen for language changes dispatched by AdvertisingAgent
  useEffect(() => {
    const handler = (e) => setLang(e.detail || 'he');
    window.addEventListener('adv_lang_change', handler);
    return () => window.removeEventListener('adv_lang_change', handler);
  }, []);

  const t = PAGE_TEXT[lang] || PAGE_TEXT.he;

  return (
    <div className="adv-page" dir={t.dir}>
      <div className="adv-page-header">
        <h1>{t.title}</h1>
        <p>{t.subtitle}</p>
      </div>
      <div className="adv-page-content">
        <AdvertisingAgent />
      </div>
    </div>
  );
}
