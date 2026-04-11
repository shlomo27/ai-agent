/**
 * weeklyEmailCron.js — Schedules the weekly marketing report email.
 *
 * Runs every Sunday at 08:00 Israel time (UTC+3 → 05:00 UTC).
 * Import and call `startWeeklyEmailCron()` once from your server.js entry point.
 *
 * Requires: node-cron
 *   npm install node-cron
 */

let cron;
try {
  cron = require('node-cron');
} catch {
  console.warn('[weeklyEmailCron] node-cron not installed — weekly emails disabled. Run: npm install node-cron');
  module.exports = { startWeeklyEmailCron: () => {} };
  return;
}

const { sendWeeklyReports } = require('../services/weeklyEmailReport');

// Cron expression: "0 5 * * 0" = every Sunday at 05:00 UTC (08:00 Israel)
const CRON_SCHEDULE = process.env.WEEKLY_EMAIL_CRON || '0 5 * * 0';

function startWeeklyEmailCron() {
  if (!cron.validate(CRON_SCHEDULE)) {
    console.error(`[weeklyEmailCron] Invalid cron schedule: ${CRON_SCHEDULE}`);
    return;
  }

  const task = cron.schedule(CRON_SCHEDULE, async () => {
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

  console.log(`[weeklyEmailCron] Scheduled weekly emails — ${CRON_SCHEDULE} (Asia/Jerusalem)`);
  return task;
}

module.exports = { startWeeklyEmailCron };
