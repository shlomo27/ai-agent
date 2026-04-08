/**
 * App.jsx — Updated routing for ilmariai.com
 *
 * Changes vs original:
 *  - Added /advertising/dashboard route (AdvertisingDashboard)
 *  - /advertising route already existed (AdvertisingPage)
 *
 * Instructions:
 *  1. Copy AdvertisingDashboard.jsx → appify/frontend/src/pages/
 *  2. Add the two import lines and the Route below to your existing App.jsx
 *
 * Minimal diff to add to your existing App.jsx:
 * ─────────────────────────────────────────────
 * import AdvertisingDashboard from "./pages/AdvertisingDashboard";
 *
 * // Inside <Routes>:
 * <Route path="/advertising/dashboard" element={<PrivateRoute><AdvertisingDashboard /></PrivateRoute>} />
 * ─────────────────────────────────────────────
 */

import LandingPage from "./pages/LandingPage";
import React from "react";
import { Helmet } from "react-helmet";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider, useAuth } from "./context/AuthContext";
import Dashboard from "./pages/Dashboard";
import AppBuilder from "./pages/AppBuilder";
import PublicSite from "./pages/PublicSite";
import Preview from "./pages/Preview";
import Login from "./pages/Login";
import Register from "./pages/Register";
import Pricing from "./pages/Pricing";
import PaymentSuccess from "./pages/PaymentSuccess";
import AdminPanel from "./pages/AdminPanel";
import Contact from "./pages/Contact";
import ResetPassword from "./pages/ResetPassword";
import Terms from "./pages/Terms";
import Privacy from "./pages/Privacy";
import Refund from "./pages/Refund";
import AdvertisingPage from "./pages/AdvertisingPage";
import AdvertisingDashboard from "./pages/AdvertisingDashboard"; // ← NEW

// Protected route - redirects to login if not authenticated
function PrivateRoute({ children }) {
  const { user, loading } = useAuth();
  if (loading) return (
    <div style={{ minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center", fontFamily: "sans-serif", color: "#6b7280" }}>
      Loading...
    </div>
  );
  return user ? children : <Navigate to="/login" replace />;
}

// Guest route - redirects to home if already logged in
function GuestRoute({ children }) {
  const { user, loading } = useAuth();
  if (loading) return null;
  return !user ? children : <Navigate to="/" replace />;
}

function AppRoutes() {
  return (
    <Routes>
      {/* Landing page - public, always */}
      <Route path="/" element={<LandingPage />} />

      {/* Dashboard - only for logged in users */}
      <Route path="/dashboard" element={<PrivateRoute><Dashboard /></PrivateRoute>} />

      {/* Auth */}
      <Route path="/login" element={<GuestRoute><Login /></GuestRoute>} />
      <Route path="/register" element={<GuestRoute><Register /></GuestRoute>} />

      {/* Public routes */}
      <Route path="/preview/:id" element={<Preview />} />
      <Route path="/site/:id" element={<PublicSite />} />
      <Route path="/pricing" element={<Pricing />} />
      <Route path="/payment/success" element={<PaymentSuccess />} />
      <Route path="/admin2" element={<PrivateRoute><AdminPanel /></PrivateRoute>} />
      <Route path="/reset-password" element={<ResetPassword />} />
      <Route path="/contact" element={<Contact />} />
      <Route path="/terms" element={<Terms />} />
      <Route path="/privacy" element={<Privacy />} />
      <Route path="/refund" element={<Refund />} />

      {/* Advertising */}
      <Route path="/advertising" element={<PrivateRoute><AdvertisingPage /></PrivateRoute>} />
      <Route path="/advertising/dashboard" element={<PrivateRoute><AdvertisingDashboard /></PrivateRoute>} /> {/* ← NEW */}

      {/* Builder - protected */}
      <Route path="/builder/:key" element={<PrivateRoute><AppBuilder /></PrivateRoute>} />

      {/* Fallback */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <Helmet>
        <title>Ilmari AI | No-Code AI App Builder</title>
        <meta name="description" content="Build AI-powered apps and websites without writing a single line of code." />
      </Helmet>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </BrowserRouter>
  );
}
