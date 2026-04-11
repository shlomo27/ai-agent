/**
 * weeklyEmailReport.js — Weekly summary email service for AI Marketing users.
 *
 * Called by a cron job every Sunday morning.
 * Fetches weekly report data from the AI Agent, then sends a Hebrew summary
 * email via Resend to each eligible user.
 *
 * Eligible users: marketing_plan is basic / pro / business / bundle_*
 * (Free plan users do NOT receive weekly emails)
 *
 * Environment vars required (in appify):
 *   RESEND_API_KEY       — Resend API key
 *   RESEND_FROM_EMAIL    — Sender address (e.g. reports@ilmariai.com)
 *   AI_AGENT_URL         — Base URL of the AI Agent API
 */

const { Resend } = require('resend');
const User = require('../models/User');

const AI_AGENT_URL = process.env.AI_AGENT_URL || 'https://ai-agent-production-bf7b.up.railway.app';
const FROM_EMAIL = process.env.RESEND_FROM_EMAIL || 'reports@ilmariai.com';

const PAID_PLANS = ['basic', 'pro', 'business', 'bundle_starter', 'bundle_pro', 'bundle_business'];

// ─── Fetch report data from AI Agent ─────────────────────────────────────────
async function fetchWeeklyReportData(userId) {
  try {
    const res = await fetch(`${AI_AGENT_URL}/api/weekly-email/${userId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      signal: AbortSignal.timeout(10000),
    });
    if (!res.ok) return null;
    return await res.json();
  } catch (err) {
    console.error(`[weeklyEmail] Failed to fetch report for ${userId}:`, err.message);
    return null;
  }
}

// ─── Build HTML email ─────────────────────────────────────────────────────────
function buildEmailHtml(data) {
  const { business_name, report } = data;
  const name = business_name || 'העסק שלך';
  const exec = report.executive_summary || {};
  const plan = report.next_week_plan || {};
  const actions = report.action_items || [];
  const insights = report.insights || [];

  const gradeColor = exec.grade === 'A' ? '#22c55e' : exec.grade === 'B' ? '#f59e0b' : '#ef4444';

  const actionItems = actions
    .map(a => `<li style="margin:6px 0;color:#374151;">${a}</li>`)
    .join('');

  const insightItems = insights
    .map(i => `<li style="margin:6px 0;color:#374151;">${i}</li>`)
    .join('');

  const upcomingPosts = (data.scheduled_upcoming || [])
    .map(p => `<li style="margin:4px 0;color:#6b7280;font-size:13px;">📅 ${p.scheduled_for ? new Date(p.scheduled_for).toLocaleDateString('he-IL') : 'בקרוב'} — ${String(p.content || '').substring(0, 60)}...</li>`)
    .join('');

  return `
<!DOCTYPE html>
<html dir="rtl" lang="he">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>${data.email_subject}</title>
</head>
<body style="margin:0;padding:0;background:#f3f4f6;font-family:Arial,sans-serif;direction:rtl;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f3f4f6;padding:20px 0;">
    <tr>
      <td align="center">
        <table width="600" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:12px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.08);">

          <!-- Header -->
          <tr>
            <td style="background:linear-gradient(135deg,#7c3aed,#4f46e5);padding:32px 40px;text-align:right;">
              <div style="color:#c4b5fd;font-size:13px;margin-bottom:4px;">ilmariai.com — עוזר הפרסום החכם</div>
              <h1 style="color:#ffffff;margin:0;font-size:24px;">סיכום שבועי</h1>
              <div style="color:#ddd6fe;font-size:15px;margin-top:4px;">📊 ${name}</div>
              <div style="color:#a78bfa;font-size:12px;margin-top:6px;">${report.period || ''}</div>
            </td>
          </tr>

          <!-- Performance Score -->
          <tr>
            <td style="padding:32px 40px 16px;">
              <table width="100%" cellpadding="0" cellspacing="0">
                <tr>
                  <td style="background:#f9fafb;border-radius:10px;padding:20px;text-align:center;">
                    <div style="font-size:48px;font-weight:bold;color:${gradeColor};">${exec.grade || 'B'}</div>
                    <div style="color:#6b7280;font-size:14px;">ציון ביצועים</div>
                    <div style="color:#9ca3af;font-size:12px;margin-top:4px;">${exec.performance_score || 0}/100</div>
                  </td>
                  <td width="20"></td>
                  <td style="background:#f9fafb;border-radius:10px;padding:20px;" width="350">
                    <table width="100%">
                      <tr>
                        <td style="color:#6b7280;font-size:13px;">פוסטים שפורסמו</td>
                        <td style="color:#111827;font-weight:bold;text-align:left;">${exec.posts_published || 0}</td>
                      </tr>
                      <tr><td colspan="2" style="padding:4px 0;"></td></tr>
                      <tr>
                        <td style="color:#6b7280;font-size:13px;">פלטפורמות פעילות</td>
                        <td style="color:#111827;font-weight:bold;text-align:left;">${exec.platforms_active || 0}</td>
                      </tr>
                      <tr><td colspan="2" style="padding:4px 0;"></td></tr>
                      <tr>
                        <td style="color:#6b7280;font-size:13px;">חשיפה משוערת</td>
                        <td style="color:#111827;font-weight:bold;text-align:left;">${(exec.estimated_reach || 0).toLocaleString()}</td>
                      </tr>
                    </table>
                  </td>
                </tr>
              </table>
            </td>
          </tr>

          <!-- Insights -->
          ${insightItems ? `
          <tr>
            <td style="padding:8px 40px 16px;">
              <h2 style="color:#111827;font-size:17px;margin:0 0 12px;">💡 תובנות השבוע</h2>
              <ul style="margin:0;padding:0 20px;">${insightItems}</ul>
            </td>
          </tr>` : ''}

          <!-- Next week plan -->
          <tr>
            <td style="padding:8px 40px 16px;">
              <h2 style="color:#111827;font-size:17px;margin:0 0 12px;">🗓️ תכנית השבוע הבא</h2>
              <table width="100%" style="background:#f0fdf4;border-radius:8px;padding:16px;" cellpadding="0" cellspacing="0">
                <tr>
                  <td style="color:#166534;font-size:14px;">📌 פוסטים מומלצים: <strong>${plan.recommended_posts || 14}</strong></td>
                </tr>
                <tr><td style="padding:4px 0;"></td></tr>
                <tr>
                  <td style="color:#166534;font-size:14px;">🎯 מטרה: ${plan.goal || 'הגדל reach'}</td>
                </tr>
              </table>
            </td>
          </tr>

          <!-- Upcoming scheduled -->
          ${upcomingPosts ? `
          <tr>
            <td style="padding:8px 40px 16px;">
              <h2 style="color:#111827;font-size:17px;margin:0 0 12px;">⏰ פוסטים מתוזמנים</h2>
              <ul style="margin:0;padding:0 20px;">${upcomingPosts}</ul>
            </td>
          </tr>` : ''}

          <!-- Action items -->
          ${actionItems ? `
          <tr>
            <td style="padding:8px 40px 16px;">
              <h2 style="color:#111827;font-size:17px;margin:0 0 12px;">✅ משימות לביצוע</h2>
              <ul style="margin:0;padding:0 20px;">${actionItems}</ul>
            </td>
          </tr>` : ''}

          <!-- CTA -->
          <tr>
            <td style="padding:24px 40px 32px;text-align:center;">
              <a href="https://ilmariai.com/advertising/dashboard"
                 style="display:inline-block;background:linear-gradient(135deg,#7c3aed,#4f46e5);color:#ffffff;text-decoration:none;padding:14px 32px;border-radius:8px;font-size:15px;font-weight:bold;">
                פתח את לוח הבקרה ←
              </a>
            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td style="background:#f9fafb;padding:20px 40px;text-align:center;border-top:1px solid #e5e7eb;">
              <p style="color:#9ca3af;font-size:12px;margin:0;">
                נשלח על ידי <a href="https://ilmariai.com" style="color:#7c3aed;text-decoration:none;">ilmariai.com</a>
                &nbsp;·&nbsp;
                <a href="https://ilmariai.com/unsubscribe" style="color:#9ca3af;">הסר מרשימת התפוצה</a>
              </p>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>
</body>
</html>`;
}

// ─── Send email via Resend ────────────────────────────────────────────────────
async function sendEmailViaResend(to, subject, html) {
  if (!process.env.RESEND_API_KEY) {
    console.warn('[weeklyEmail] RESEND_API_KEY not set — skipping send');
    return false;
  }
  try {
    const resend = new Resend(process.env.RESEND_API_KEY);
    const { error } = await resend.emails.send({ from: FROM_EMAIL, to, subject, html });
    if (error) {
      console.error(`[weeklyEmail] Resend error for ${to}:`, error.message);
      return false;
    }
    return true;
  } catch (err) {
    console.error(`[weeklyEmail] Network error sending to ${to}:`, err.message);
    return false;
  }
}

// ─── Main: send reports to all eligible users ─────────────────────────────────
async function sendWeeklyReports() {
  console.log('[weeklyEmail] Starting weekly report job...');

  const users = await User.find({
    marketing_plan: { $in: PAID_PLANS },
    email: { $exists: true, $ne: '' },
  }).select('_id email marketing_plan').lean();

  console.log(`[weeklyEmail] Found ${users.length} eligible users`);

  let sent = 0;
  let failed = 0;

  for (const user of users) {
    try {
      const data = await fetchWeeklyReportData(String(user._id));
      if (!data || !data.report) {
        console.warn(`[weeklyEmail] No report data for user ${user._id}`);
        failed++;
        continue;
      }

      const html = buildEmailHtml(data);
      const ok = await sendEmailViaResend(user.email, data.email_subject, html);
      if (ok) {
        sent++;
        console.log(`[weeklyEmail] ✅ Sent to ${user.email}`);
      } else {
        failed++;
      }

      // Throttle: 1 email per 200ms to respect Resend rate limits
      await new Promise(r => setTimeout(r, 200));
    } catch (err) {
      console.error(`[weeklyEmail] Error for user ${user._id}:`, err.message);
      failed++;
    }
  }

  console.log(`[weeklyEmail] Done. Sent: ${sent}, Failed: ${failed}`);
  return { sent, failed, total: users.length };
}

module.exports = { sendWeeklyReports, buildEmailHtml, sendEmailViaResend, fetchWeeklyReportData };
