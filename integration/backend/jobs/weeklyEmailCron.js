/**
 * weeklyEmailCron.js — Schedules the weekly marketing report email.
 *
 * Runs every Sunday at 08:00 Israel time (UTC+3 → 05:00 UTC).
 * Import and call `startWeeklyEmailCron()` once from your server.js entry point.
 *
 * Compatible with node-cron v3 and v4.
 */

const cron = require('node-cron');
const { sendWeeklyReports } = require('../services/weeklyEmailReport');

// Cron expression: "0 5 * * 0" = every Sunday at 05:00 UTC (08:00 Israel)
const CRON_SCHEDULE = process.env.WEEKLY_EMAIL_CRON || '0 5 * * 0';

function startWeeklyEmailCron() {
  try {
    cron.schedule(CRON_SCHEDULE, async () => {
      console.log('[weeklyEmailCron] 🕐 Firing weekly email job...');
      try {
        const result = await sendWeeklyReports();
        console.log(`[weeklyEmailCron] ✅ Completed: ${result.sent} sent, ${result.failed} failed`);
      } catch (err) {
        console.error('[weeklyEmailCron] ❌ Job error:', err.message);
      }
    }, {
      timezone: 'Asia/Jerusalem',
    });

    console.log(`[weeklyEmailCron] ✅ Scheduled weekly emails — every Sunday 08:00 Israel time`);
  } catch (err) {
    console.error('[weeklyEmailCron] Failed to schedule:', err.message);
  }
}

module.exports = { startWeeklyEmailCron };
