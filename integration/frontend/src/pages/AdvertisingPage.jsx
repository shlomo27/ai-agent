import AdvertisingAgent from '../components/AdvertisingAgent';
import './AdvertisingPage.css';

export default function AdvertisingPage() {
  return (
    <div className="adv-page">
      <div className="adv-page-header">
        <h1>🚀 עוזר פרסום חכם</h1>
        <p>פרסם ברשתות חברתיות, צור קמפיינים ונתח ביצועים — הכל בעזרת AI</p>
      </div>
      <div className="adv-page-content">
        <AdvertisingAgent />
      </div>
    </div>
  );
}
