# מדריך שילוב עוזר פרסום ב-appify

## שלב 1 - העתק קבצים

### Backend:
העתק את `backend/routes/advertising.js` לתיקיית `backend/routes/` ב-appify.

### Frontend:
- העתק את `frontend/src/components/AdvertisingAgent.jsx` ו-`AdvertisingAgent.css` לתיקיית `frontend/src/components/`
- העתק את `frontend/src/pages/AdvertisingPage.jsx` ו-`AdvertisingPage.css` לתיקיית `frontend/src/pages/`

---

## שלב 2 - הוסף Route ב-server.js

פתח `backend/server.js` והוסף לאחר שאר ה-imports:
```js
const advertisingRouter = require('./routes/advertising');
```

והוסף לאחר שאר ה-routes (לפני MongoDB connection):
```js
app.use('/api/advertising', advertisingRouter);
```

---

## שלב 3 - הוסף ל-App.jsx

פתח `frontend/src/App.jsx` והוסף:
```jsx
import AdvertisingPage from './pages/AdvertisingPage';

// בתוך ה-Routes הוסף:
<Route path="/advertising" element={<AdvertisingPage />} />
```

---

## שלב 4 - הוסף לניווט

בקומפוננט הניווט של appify, הוסף קישור:
```jsx
<a href="/advertising">🚀 עוזר פרסום</a>
```

---

## שלב 5 - הוסף משתנה סביבה ב-Railway

ב-Railway → appify → Variables, הוסף:
```
AI_AGENT_URL=https://ai-agent-production-bf7b.up.railway.app
```

---

זהו! עוזר הפרסום יהיה זמין בכתובת `/advertising` באפליקציה שלך.
