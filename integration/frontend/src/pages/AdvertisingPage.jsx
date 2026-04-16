import { useState, useEffect } from 'react';
import AdvertisingAgent from '../components/AdvertisingAgent';
import SocialConnect from '../components/SocialConnect';
import './AdvertisingPage.css';

export default function AdvertisingPage() {
  const [lang, setLang] = useState(() => localStorage.getItem('adv_lang') || 'he');
  const [connectOpen, setConnectOpen] = useState(
    () => localStorage.getItem('adv_connect_open') !== 'false'
  );

  useEffect(() => {
    const handler = (e) => setLang(e.detail || 'he');
    window.addEventListener('adv_lang_change', handler);
    return () => window.removeEventListener('adv_lang_change', handler);
  }, []);

  const handleLangChange = (newLang) => setLang(newLang);

  const toggleConnect = () => {
    const next = !connectOpen;
    setConnectOpen(next);
    localStorage.setItem('adv_connect_open', String(next));
  };

  const isRtl = lang === 'he';

  return (
    <div className="adv-page" dir={isRtl ? 'rtl' : 'ltr'}>
      {/* Collapsible social connect panel */}
      <div className="adv-connect-wrapper">
        <button className="adv-connect-toggle" onClick={toggleConnect}>
          <span>🔗 {lang === 'he' ? 'חיבור פלטפורמות' : 'Connect Platforms'}</span>
          <span className="adv-toggle-arrow">{connectOpen ? '▲' : '▼'}</span>
        </button>
        {connectOpen && (
          <div className="adv-connect-body">
            <SocialConnect language={lang} />
          </div>
        )}
      </div>

      {/* Chat */}
      <div className="adv-page-content">
        <AdvertisingAgent language={lang} onLanguageChange={handleLangChange} />
      </div>
    </div>
  );
}
