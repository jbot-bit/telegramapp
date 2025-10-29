# VOUCH PORTAL — VIRAL GROWTH & RETENTION LOOPS (Claude Instruction Set 3 of 4)

## GOAL
Drive organic usage inside Telegram without spam. Use reciprocity, status, and social proof. Keep all group posts neutral.

---

## CORE SAFE LOOPS

### 1) Mutual-Vouch Loop
- Trigger after a user receives a vouch:
  - UI toast: “💬 Return the favor?” → opens prefilled vouch modal to the same user.
- Server logs `mutual_vouch` event when reciprocated within 48h.

### 2) Rank-Share Loop
- On rank up:
  - Modal: “🎉 You’re now {badge}. Share your badge?”
  - Telegram share intent text ≤120 chars:
    - “I just reached {badge} on Vouch Portal. Build yours: t.me/{BOT_USERNAME}?startapp=profile_{TG_ID}”
- Track referral source via `startapp` payload.

### 3) Invite-to-Verify Loop
- “Request Vouch” → bot sends ONE polite DM to each nominated handle:
  - “👋 @{claimer} invited you to verify them on Vouch Portal.” [Open Profile]
- No repeats within 7 days per voucher handle.

### 4) Top Helpers Loop
- Weekly board (inside app + optional neutral group post):
  - “🏆 Top Helpers This Week: @a, @b, @c”
- Soft badge persists for 7 days on their profiles.

---

## SECONDARY MECHANICS

- **Progress pressure:** “Only {n} to reach {next_badge}”
- **Recent activity ticker:** “+{N} vouches today”
- **Streaks:** 🔥 shows after 3 consecutive active days (resets weekly)
- **Micro-rewards:** confetti + subtle haptics on milestones

---

## COPY TONE (SAFE)
- Positive, neutral, communal.
- Avoid: “scam”, “fraud”, “report”, “rating”, “review”.
- Use: “trust”, “verify”, “build reputation”, “community”.

**Templates**
- Group CTA: “🧾 @{user} is seeking community vouches — Open profile.”
- Rank-up: “✅ @{user} reached *{badge}* (confirmed vouches: {count}).”
- DM invite: “👋 @{claimer} invited you to verify them. Tap below.”

---

## REFERRALS

### Link format
- `t.me/{BOT_USERNAME}?startapp=ref_{referrer_id}`
- On first open:
  - Store `referrer_id` if new user.
  - Attribute any later rank-ups to referrer for scoring.

### UI hooks
- After rank-up or first verification:
  - Modal with copyable link + “Share” button.

---

## RATE LIMITS / ANTI-SPAM
- DM invites: max 1 per voucher handle every 7 days.
- No unsolicited DMs otherwise.
- Group posts:
  - Rank-ups: allowed.
  - Digest: every 12h, delete previous digest first.
- Share prompts: user-initiated only.

---

## EVENTS TO LOG
- `rank_up`, `mutual_vouch`, `referral_click`, `referral_signup`
- `invite_sent`, `invite_cooldown_blocked`
- `share_prompt_shown`, `share_clicked`

---

## SIMPLE IMPLEMENTATION NOTES

### Frontend
- After any vouch received → show “Return the favor?” CTA with 1-tap.
- On rank-up → show share modal (copy + share intent).
- Streak logic client-side + server-confirmed.

### Backend
- Parse `startapp` payloads for ref tracking.
- Enforce invite cooldowns per handle.
- Store weekly helper tallies (distinct targets vouched for).
- Expose `/api/viral/summary` for UI ticker.

---

## OUTPUT REQUEST (from Claude)
- JS: share intent + mutual-vouch CTA modules.
- FastAPI routes for referral capture + viral summaries.
- Bot handlers for DM invites with inline “Open Profile” button.
- Neutral copy strings as constants.
- Weekly job for Top Helpers + optional group announcement (with last-message cleanup).

---

End of `3_viral_growth_loops.md`
