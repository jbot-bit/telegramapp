# VOUCH PORTAL — CORE APP BUILD GUIDE (Claude Instruction Set 1 of 4)

## OBJECTIVE
Create a **Telegram Mini WebApp** + **FastAPI backend** that lets users:
- View and manage trust profiles.
- Give and receive vouches.
- Track rank progress and reputation.
- Sync all data through PostgreSQL.

All hosted on **Replit** (low-cost, mobile-optimized).

---

## ARCHITECTURE OVERVIEW
- **Backend:** FastAPI (Python 3.12)
- **Frontend:** HTML + Tailwind (or minimal CSS)
- **Database:** PostgreSQL (Replit Database or external Postgres)
- **Bot Connection:** Telegram Bot API via Webhook
- **WebApp Client:** Served via `/` route
- **Storage:** Postgres tables for users, vouches, config, analytics

---

## REQUIRED FILES
/main.py -> FastAPI app, webhook, and routes
/bot.py -> Telegram handlers (python-telegram-bot)
/database.py -> asyncpg connection + schema
/webapp/index.html -> Frontend (mobile webapp)
/webapp/static/ -> CSS + JS
/config.env -> Environment vars (API keys, DB URL)

yaml
Copy code

---

## ENVIRONMENT VARIABLES
Set these in Replit “Secrets”:
BOT_TOKEN=xxxxxxxxxxxxxx
WEBHOOK_URL=https://suncoastvouchbot.replit.app
DATABASE_URL=postgresql://user:password@host:port/dbname
ADMIN_ID=123456789 # Your Telegram ID

yaml
Copy code

---

## DATABASE STRUCTURE

### `users`
| Field | Type | Notes |
|-------|------|-------|
| telegram_user_id | BIGINT | Primary key |
| username | TEXT |  |
| first_seen_at | TIMESTAMP |  |
| total_vouches | INT | default 0 |
| rank | TEXT | stored rank name |
| last_active_at | TIMESTAMP |  |

### `vouches`
| Field | Type | Notes |
|-------|------|-------|
| id | SERIAL | Primary key |
| from_user_id | BIGINT | FK users |
| to_user_id | BIGINT | FK users |
| message | TEXT |  |
| created_at | TIMESTAMP | default now() |
| approved | BOOLEAN | default false |

### `bot_config`
| key | value | updated_at |

---

## ENDPOINTS

| Route | Method | Description |
|-------|---------|-------------|
| `/` | GET | Serves WebApp |
| `/webhook` | POST | Handles Telegram webhook updates |
| `/api/users` | GET | Returns user list |
| `/api/profile/{id}` | GET | Returns user profile |
| `/api/vouch` | POST | Submit new vouch |
| `/health` | GET | Health check |

---

## WEBHOOK SETUP
Once deployed:
```bash
curl "https://api.telegram.org/bot<YOUR_TOKEN>/setWebhook?url=https://suncoastvouchbot.replit.app/webhook"
Confirm with:

bash
Copy code
curl "https://api.telegram.org/bot<YOUR_TOKEN>/getWebhookInfo"
You should see:

json
Copy code
{"ok":true,"result":{"url":"https://suncoastvouchbot.replit.app/webhook","pending_update_count":0}}
BASIC BOT FLOW
User joins Telegram group → /start

Bot checks DB → creates user record

Bot posts public message:

css
Copy code
🧾 @username joined. Do you vouch for them?
Buttons:

👍 Yes

⚠️ Unsure

Votes saved to DB

Rank auto-updates based on total vouches

WebApp shows profile, vouches, rank progress

RANK SYSTEM
Range	Rank	Emoji
0–2	🚫 Unverified	
3–5	✅ Verified	
6–10	🔷 Trusted	
11–15	🛡 Endorsed	
16+	👑 Top-Tier Verified	

FRONTEND FEATURES
Responsive mobile-first layout

Profile card for each user

“Give Vouch” and “Request Vouch” buttons

Dynamic progress bar for rank

Inline disclaimer:

“Community opinions only. Be respectful.”

DISMISS REPORT RISKS
No “scam” or “fraud” text in UI

Disclaimers on any content visible to public

Use positive framing (“Trust”, “Reputation”)

Disable images or links in user-submitted text

Auto-sanitize banned terms to [redacted]

SECURITY
All DB writes through parameterized queries

Verify webhook source IP

Admin-only access to /admin/* endpoints

TLS via Replit auto HTTPS

OUTPUT REQUEST
Claude should output:

Full main.py and bot.py

Minimal frontend HTML/CSS

SQL schema setup commands

Instructions for setting environment variables

Basic README text

End of 1_core_app_build.md