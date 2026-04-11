/**
 * User.js — Updated model for ilmariai.com
 *
 * Changes vs original:
 *  - Added `marketing_plan` field (AI Marketing subscription track)
 *  - Added `paddleCustomerId` field
 *  - Added `socialTokens` for OAuth platform connections
 *  - PLAN_CREDITS updated to reflect both tracks
 *
 * Instructions:
 *  Replace your existing backend/models/User.js with this file.
 *  Then run: node -e "require('./models/User')" to verify no errors.
 */

const mongoose = require('mongoose');
const bcrypt = require('bcryptjs');

// ─── Credits per AIBuilder plan ───────────────────────────────────────────────
const PLAN_CREDITS = {
  free: 10,
  starter: 100,
  pro: 350,
};

// ─── Daily message limits per Marketing plan ──────────────────────────────────
const MARKETING_DAILY_LIMITS = {
  free:            10,
  basic:           30,
  pro:            100,
  business:       200,
  bundle_starter:  20,
  bundle_pro:      75,
  bundle_business:200,
};

const userSchema = new mongoose.Schema(
  {
    name:     { type: String },
    username: { type: String },
    email:    { type: String, required: true, unique: true },
    password: { type: String, required: true },
    isAdmin:  { type: Boolean, default: false },

    // ── AIBuilder plan (existing) ────────────────────────────────────────────
    plan: {
      type: String,
      enum: ['free', 'starter', 'pro'],
      default: 'free',
    },

    // ── AI Marketing plan (new) ──────────────────────────────────────────────
    marketing_plan: {
      type: String,
      enum: ['free', 'basic', 'pro', 'business', 'bundle_starter', 'bundle_pro', 'bundle_business'],
      default: 'free',
    },

    // ── Credits (AIBuilder) ──────────────────────────────────────────────────
    credits: { type: Number, default: 10 },
    creditsLastReset: { type: Date, default: Date.now },

    // ── Paddle billing ───────────────────────────────────────────────────────
    paddleCustomerId:    { type: String },
    paddleSubscriptionId:{ type: String },

    // ── Stripe (legacy — keep for migration period) ──────────────────────────
    stripeCustomerId:     { type: String },
    stripeSubscriptionId: { type: String },

    subscriptionStatus: {
      type: String,
      default: 'inactive', // active / inactive / canceled / cancel_scheduled
    },

    // ── Google OAuth ─────────────────────────────────────────────────────────
    googleId: { type: String },

    // ── Social platform tokens (for AI Marketing posting) ────────────────────
    // Each entry: { platform, accessToken, pageId, pageName, expiresAt }
    socialTokens: [
      {
        platform:    { type: String }, // facebook / instagram / twitter / linkedin / tiktok
        accessToken: { type: String },
        refreshToken:{ type: String },
        pageId:      { type: String },
        pageName:    { type: String },
        expiresAt:   { type: Date },
        connectedAt: { type: Date, default: Date.now },
      },
    ],

    // ── Forgot Password ──────────────────────────────────────────────────────
    resetPasswordToken:   { type: String },
    resetPasswordExpires: { type: Date },

    // ── AIBuilder usage ──────────────────────────────────────────────────────
    buildsUsed:  { type: Number, default: 0 },
    buildsLimit: { type: Number, default: 10 },
  },
  { timestamps: true }
);

// ─── Password hashing ─────────────────────────────────────────────────────────
userSchema.pre('save', async function (next) {
  if (!this.isModified('password')) return next();
  const salt = await bcrypt.genSalt(10);
  this.password = await bcrypt.hash(this.password, salt);
  next();
});

userSchema.methods.matchPassword = async function (enteredPassword) {
  return bcrypt.compare(enteredPassword, this.password);
};
userSchema.methods.comparePassword = async function (plain) {
  return bcrypt.compare(plain, this.password);
};

// ─── Credits helpers ──────────────────────────────────────────────────────────
userSchema.methods.hasCredits = function (amount = 1) {
  return this.credits >= amount;
};
userSchema.methods.deductCredits = async function (amount = 1) {
  this.credits = Math.max(0, this.credits - amount);
  await this.save();
};
userSchema.statics.getCreditsForPlan = function (plan) {
  return PLAN_CREDITS[plan] || 10;
};

// Resets credits to plan maximum if 30+ days have passed since last reset
userSchema.methods.resetCreditsIfNeeded = async function () {
  const now = new Date();
  const lastReset = this.creditsLastReset || new Date(0);
  const daysSince = (now - lastReset) / (1000 * 60 * 60 * 24);
  if (daysSince >= 30) {
    this.credits = PLAN_CREDITS[this.plan] || 10;
    this.creditsLastReset = now;
    await this.save();
    return true;
  }
  return false;
};

// ─── Marketing helpers ────────────────────────────────────────────────────────
userSchema.methods.getMarketingDailyLimit = function () {
  return MARKETING_DAILY_LIMITS[this.marketing_plan] || 10;
};

// ─── Social token helpers ─────────────────────────────────────────────────────
userSchema.methods.getSocialToken = function (platform) {
  return this.socialTokens.find(t => t.platform === platform) || null;
};

userSchema.methods.setSocialToken = async function (platform, tokenData) {
  const idx = this.socialTokens.findIndex(t => t.platform === platform);
  if (idx >= 0) {
    this.socialTokens[idx] = { platform, ...tokenData, connectedAt: new Date() };
  } else {
    this.socialTokens.push({ platform, ...tokenData, connectedAt: new Date() });
  }
  await this.save();
};

userSchema.methods.removeSocialToken = async function (platform) {
  this.socialTokens = this.socialTokens.filter(t => t.platform !== platform);
  await this.save();
};

module.exports = mongoose.model('User', userSchema);
module.exports.PLAN_CREDITS = PLAN_CREDITS;
module.exports.MARKETING_DAILY_LIMITS = MARKETING_DAILY_LIMITS;
