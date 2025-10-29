# 🤝 Vouch Portal - Telegram Mini WebApp

A community trust and reputation system built as a Telegram Mini WebApp. Users can vouch for each other, build reputation, and establish trust within the community.

## Features

### Core Features
- **User Profiles** - View and manage your trust profile
- **Vouch System** - Give and receive vouches from community members
- **Rank Progression** - Advance through 5 reputation tiers
- **Community Directory** - Browse and search all users
- **Analytics Dashboard** - Admin insights into community health

### Rank System
- 🚫 **Unverified** (0-2 vouches)
- ✅ **Verified** (3-5 vouches)
- 🔷 **Trusted** (6-10 vouches)
- 🛡 **Endorsed** (11-15 vouches)
- 👑 **Top-Tier Verified** (16+ vouches)

### Viral Growth Features
- Referral tracking via deep links
- Mutual-vouch prompts
- Rank-up sharing
- Weekly top helpers leaderboard
- Invite system with rate limiting

## Tech Stack

- **Backend:** FastAPI (Python 3.12)
- **Frontend:** HTML5 + CSS3 + Vanilla JavaScript
- **Database:** PostgreSQL with asyncpg
- **Bot:** python-telegram-bot
- **Hosting:** Replit (or any cloud platform)

## Project Structure

```
telegramapp/
├── main.py                 # FastAPI application & API endpoints
├── bot.py                  # Telegram bot handlers & commands
├── database.py             # PostgreSQL connection & queries
├── requirements.txt        # Python dependencies
├── .env.example           # Environment variables template
├── .replit                # Replit configuration
├── pyproject.toml         # Python project metadata
├── README.md              # This file
└── webapp/
    ├── index.html         # Main WebApp interface
    └── static/
        ├── styles.css     # Dark theme styling
        └── main.js        # Client-side logic
```

## Setup Instructions

### 1. Create a Telegram Bot

1. Message [@BotFather](https://t.me/BotFather) on Telegram
2. Send `/newbot` and follow the prompts
3. Save your bot token
4. Send `/setdomain` to set your WebApp URL
5. Send `/setmenubutton` to add a "Open App" button

### 2. Setup Database

**Option A: Replit Database**
- Use Replit's built-in PostgreSQL database
- Get connection string from Replit dashboard

**Option B: External PostgreSQL**
- Use any PostgreSQL provider (Supabase, Neon, Railway, etc.)
- Get your DATABASE_URL connection string

### 3. Configure Environment Variables

Create a `.env` file (or use Replit Secrets):

```env
BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
BOT_USERNAME=YourBotUsername
WEBHOOK_URL=https://your-app.replit.app
ADMIN_ID=123456789
DATABASE_URL=postgresql://user:pass@host:5432/dbname
PORT=8080
```

**How to get your ADMIN_ID:**
1. Message [@userinfobot](https://t.me/userinfobot) on Telegram
2. It will send you your Telegram user ID

### 4. Deploy on Replit

1. Create a new Repl
2. Import from GitHub or upload files
3. Install dependencies: `pip install -r requirements.txt`
4. Add secrets in the Secrets tab (Environment variables)
5. Click "Run" - Replit will:
   - Install dependencies
   - Start the FastAPI server
   - Expose a public URL

### 5. Set Webhook

Once your app is running, set the Telegram webhook:

```bash
curl "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook?url=https://your-app.replit.app/webhook"
```

Verify it worked:

```bash
curl "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getWebhookInfo"
```

You should see your webhook URL in the response.

### 6. Test Your Bot

1. Open Telegram and message your bot
2. Send `/start` to initialize your profile
3. Click "Open Vouch Portal" to launch the WebApp
4. Invite friends and start vouching!

## Bot Commands

- `/start` - Initialize your profile
- `/profile` - View your profile stats
- `/vouch @username [message]` - Vouch for someone
- `/leaderboard` - See top users
- `/stats` - View analytics (admin only)
- `/help` - Show help message

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Serve WebApp frontend |
| `/health` | GET | Health check |
| `/webhook` | POST | Telegram webhook handler |
| `/api/users` | GET | List all users |
| `/api/profile/{id}` | GET | Get user profile |
| `/api/vouch` | POST | Submit vouch |
| `/api/invite` | POST | Send invite |
| `/api/analytics` | GET | Get analytics data |
| `/api/search` | GET | Search users |
| `/api/leaderboard` | GET | Get leaderboard |

## Database Schema

### Tables

**users**
- `telegram_user_id` (BIGINT, PK)
- `username`, `first_name`, `last_name`
- `total_vouches`, `rank`
- `first_seen_at`, `last_active_at`
- `referrer_id`, `streak_days`

**vouches**
- `id` (SERIAL, PK)
- `from_user_id`, `to_user_id` (FK to users)
- `message`, `created_at`, `approved`

**events**
- Analytics tracking for user actions

**rank_events**
- History of rank changes

**invites**
- Invite tracking with rate limiting

**bot_config**
- Key-value configuration storage

## Security & Safety

### Content Moderation
- Auto-sanitizes banned words (`scam`, `fraud`, etc.)
- Message length limits (120 chars)
- Neutral, positive language throughout UI

### Rate Limiting
- Invite cooldown: 7 days per user
- No spam detection built-in
- Single vouch per user pair

### Disclaimers
- "Community opinions only"
- "Be respectful"
- "Not for financial/legal verification"
- All prominently displayed in UI

## Customization

### Change Colors
Edit `webapp/static/styles.css`:
```css
:root {
    --accent-blue: #2AABEE;
    --accent-green: #4CAF50;
    /* ... */
}
```

### Adjust Rank Thresholds
Edit `database.py` - `calculate_rank()` function:
```python
if vouch_count >= 16:
    return "top_tier"
# ...
```

### Add New Features
- Extend database schema in `database.py`
- Add API endpoints in `main.py`
- Add bot commands in `bot.py`
- Update UI in `webapp/`

## Troubleshooting

### Webhook not receiving updates
- Check webhook URL is correct and publicly accessible
- Verify bot token is correct
- Check Replit logs for errors
- Ensure webhook is set: `/getWebhookInfo`

### Database connection fails
- Verify DATABASE_URL is correct
- Check database server is running
- Ensure firewall allows connections
- Test connection with `psql` or database client

### WebApp not loading
- Check static files are in `webapp/static/`
- Verify FastAPI is serving static files correctly
- Check browser console for JavaScript errors
- Ensure Telegram WebApp script is loaded

### Users not found
- User must send `/start` to bot first
- Check database has user record
- Verify telegram_user_id matches

## Development

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp .env.example .env
# Edit .env with your values

# Run locally
python main.py
```

### Using ngrok for local testing
```bash
ngrok http 8080
# Use ngrok URL for WEBHOOK_URL
```

## Production Deployment

### Replit (Recommended)
- Already configured in `.replit`
- Auto-scales, always-on with paid plan
- Built-in database option

### Other Platforms
- **Railway:** Add `Procfile` with `web: python main.py`
- **Render:** Add `render.yaml` build config
- **Heroku:** Add `Procfile` and `runtime.txt`
- **DigitalOcean App Platform:** Use buildpack detection

## Analytics & Monitoring

The admin dashboard (`/api/analytics`) tracks:
- Total users, active users (24h/7d/30d)
- New signups, total vouches
- Rank distribution
- Top helpers & most vouched users
- Mutual vouch rate

Access via `/stats` command (admin only) or Insights tab in WebApp.

## Legal & Compliance

### Terms of Use
This is a community trust system and should not be used for:
- Financial verification
- Legal verification
- Background checks
- Official identity validation

### Data Privacy
- Only stores Telegram user data (ID, username, name)
- No personal information beyond Telegram profile
- Users can request data deletion (implement GDPR compliance separately)

### Content Policy
- Auto-filters inappropriate language
- Neutral feedback only
- No defamatory content allowed
- Admin moderation recommended

## Contributing

Feel free to fork and customize for your community!

## License

MIT License - See LICENSE file for details

## Support

For issues or questions:
- Check troubleshooting section above
- Review Telegram Bot API docs
- Check FastAPI documentation
- Open GitHub issue (if applicable)

---

**Built with ❤️ for the Telegram community**

_This app promotes peer-based trust. Do not rely on it for financial or legal verification._
