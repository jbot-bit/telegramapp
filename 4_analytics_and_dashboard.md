# VOUCH PORTAL — ANALYTICS, DASHBOARD & BACKEND TELEMETRY
*(Claude Instruction Set 4 of 4)*

## OBJECTIVE
Enable visibility into usage and engagement metrics directly within the admin dashboard — all collected ethically and anonymously.

The analytics layer should:
- Show growth and community health
- Identify top contributors
- Track rank distribution
- Highlight retention and reciprocity
- Require no user tracking beyond Telegram ID

---

## DATA POINTS TO LOG

| Category | Field | Notes |
|-----------|--------|-------|
| USER | `telegram_user_id`, `rank`, `total_vouches`, `last_active_at` | baseline metrics |
| VOUCHES | `from_user_id`, `to_user_id`, `message`, `created_at`, `approved` | raw interaction |
| RANK EVENTS | `event_type`, `old_rank`, `new_rank`, `timestamp` | for badge transitions |
| VIRAL | `referrer_id`, `invite_sent`, `mutual_vouch` | referral and invite actions |
| SESSION | `ip_country`, `device_type`, `app_version` | optional lightweight metadata |

---

## DASHBOARD LAYOUT

### 🔹 Overview Tab
- Total users
- Active users (24h, 7d, 30d)
- New signups (trendline)
- Vouches given (trendline)
- Rank distribution (pie chart)

### 🔹 Engagement Tab
- Mutual-vouch rate (%)
- Average vouches per user
- Invite-to-verification conversion
- Rank-up success rate
- Daily retention % (rolling 7 days)

### 🔹 Leaderboard Tab
- Top helpers (by distinct users vouched for)
- Most vouched users (by count)
- Longest streaks

### 🔹 System Health Tab
- DB latency
- Webhook uptime
- Last error log timestamp
- Pending updates from Telegram API

---

## VISUALS
Use a simple **Recharts.js** or **Chart.js** frontend integration.

### Example Chart Config
```js
const chartColors = {
  blue: '#2AABEE',
  green: '#4CAF50',
  yellow: '#FFC107',
  red: '#F44336'
};
