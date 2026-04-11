import { useState } from 'react';
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
  // Language state lives HERE — single source of truth for the whole page
  const [lang, setLang] = useState(() => localStorage.getItem('adv_lang') || 'he');

  const handleLangChange = (newLang) => {
    setLang(newLang);
    localStorage.setItem('adv_lang', newLang);
  };

  const t = PAGE_TEXT[lang] || PAGE_TEXT.he;

  return (
    <div className="adv-page" dir={t.dir}>
      <div className="adv-page-header">
        <h1>{t.title}</h1>
        <p>{t.subtitle}</p>
      </div>
      <div className="adv-page-content">
        {/* Pass language and the setter down — component doesn't own language state */}
        <AdvertisingAgent language={lang} onLanguageChange={handleLangChange} />
      </div>
    </div>
  );
}
