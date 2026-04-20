import { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import AdvertisingAgent from '../components/AdvertisingAgent';
import SocialConnect from '../components/SocialConnect';
import './AdvertisingPage.css';

export default function AdvertisingPage() {
  const [lang, setLang] = useState(() => localStorage.getItem('adv_lang') || 'he');
  const [connectOpen, setConnectOpen] = useState(
    () => localStorage.getItem('adv_connect_open') !== 'false'
  );
  const location = useLocation();

  // Read app context and plan from URL params
  const params = new URLSearchParams(location.search);
  const appContext = params.get('app_name') ? {
    app_name: params.get('app_name') || '',
    app_url:  params.get('app_url')  || '',
    app_desc: params.get('app_desc') || '',
  } : null;
  const urlPlan = params.get('plan') || params.get('marketing_plan') || null;

  useEffect(() => {
    const handler = (e) => setLang(e.detail || 'he');
    window.addEventListener('adv_lang_change', handler);
    return () => window.removeEventListener('adv_lang_change', handler);
  }, []);

  // Auto-open the connect panel when returning from OAuth so the toast is visible
  useEffect(() => {
    const p = new URLSearchParams(window.location.search);
    if (p.get('social_connected') || p.get('social_error')) {
      setConnectOpen(true);
      localStorage.setItem('adv_connect_open', 'true');
    }
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
      {/* Collapsible social connect sidebar */}
      <div className={`adv-connect-wrapper${connectOpen ? '' : ' collapsed'}`}>
        <button className="adv-connect-toggle" onClick={toggleConnect}>
          <span className="adv-connect-toggle-label">
            🔗 {lang === 'he' ? 'חיבור פלטפורמות' : 'Connect Platforms'}
          </span>
          <span className="adv-toggle-arrow">{connectOpen ? '◀' : '▶'}</span>
        </button>
        {connectOpen && (
          <div className="adv-connect-body">
            <SocialConnect language={lang} />
          </div>
        )}
      </div>

      {/* Chat */}
      <div className="adv-page-content">
        <AdvertisingAgent
          language={lang}
          onLanguageChange={handleLangChange}
          appContext={appContext}
          marketingPlan={urlPlan}
        />
      </div>
    </div>
  );
}
