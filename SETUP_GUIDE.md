# 🚀 Quick Setup Guide - Vouch Portal

Follow these steps to get your Telegram Mini WebApp up and running in minutes!

## Prerequisites

✅ A Telegram account
✅ Access to Replit (free account)
✅ 10 minutes of your time

---

## Step 1: Create Your Telegram Bot (5 minutes)

### 1.1 Talk to BotFather

1. Open Telegram and search for `@BotFather`
2. Send `/newbot`
3. Choose a **display name** (e.g., "Suncoast Vouch Portal")
4. Choose a **username** ending in `bot` (e.g., "SuncoastVouchBot")
5. **SAVE YOUR BOT TOKEN** - looks like: `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`

### 1.2 Configure Bot Settings

Send these commands to BotFather:

```
/setdescription
```
Paste:
```
Build trust through community vouches. Your reputation grows as people verify you. 🤝
```

```
/setabouttext
```
Paste:
```
Community trust and reputation system. Give and receive vouches to build your rank!
```

```
/setcommands
```
Paste:
```
start - Initialize your profile
profile - View your stats
vouch - Vouch for someone
leaderboard - See top users
help - Show help
```

### 1.3 Get Your Admin ID

1. Search for `@userinfobot` on Telegram
2. Send it any message
3. **SAVE YOUR ID** - it's a number like `123456789`

---

## Step 2: Setup Database (3 minutes)

### Option A: Replit Database (Easiest)

1. Go to [Replit](https://replit.com)
2. Create a new Repl
3. In the Tools panel, add "PostgreSQL"
4. Copy the connection string (starts with `postgresql://`)

### Option B: External Database (Free)

Choose one:

**Supabase** (Recommended for free tier):
1. Go to [supabase.com](https://supabase.com)
2. Create a project
3. Go to Settings → Database
4. Copy the "Connection string" (URI format)

**Neon.tech** (Also great):
1. Go to [neon.tech](https://neon.tech)
2. Create a project
3. Copy the connection string

**ElephantSQL** (Simple):
1. Go to [elephantsql.com](https://elephantsql.com)
2. Create free instance
3. Copy the URL

---

## Step 3: Deploy to Replit (2 minutes)

### 3.1 Create Replit Project

1. Go to [Replit](https://replit.com)
2. Click "Create Repl"
3. Choose "Import from GitHub" OR "Upload files"
4. If uploading: Upload all files from the `telegramapp` folder

### 3.2 Configure Secrets (Environment Variables)

In Replit, click the "Secrets" (🔒) icon in the left sidebar.

Add these secrets:

| Key | Value | Example |
|-----|-------|---------|
| `BOT_TOKEN` | Your bot token from BotFather | `1234567890:ABC...` |
| `BOT_USERNAME` | Your bot's username (without @) | `SuncoastVouchBot` |
| `WEBHOOK_URL` | Your Replit URL (see next step) | `https://yourapp.replit.app` |
| `ADMIN_ID` | Your Telegram user ID | `123456789` |
| `DATABASE_URL` | Your PostgreSQL connection string | `postgresql://user:pass@...` |

**To get your WEBHOOK_URL:**
- Click "Run" once first
- Copy the URL that appears at the top (like `https://yourapp.username.repl.co`)
- Add it as the `WEBHOOK_URL` secret
- Click "Run" again

### 3.3 Run the App

1. Click the big green "Run" button
2. Wait for dependencies to install (1-2 minutes first time)
3. You should see: `Application started successfully`

---

## Step 4: Connect Telegram to Your App (1 minute)

### 4.1 Set the Webhook

Open a new browser tab and paste this URL (replace with your values):

```
https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook?url=<YOUR_WEBHOOK_URL>/webhook
```

**Example:**
```
https://api.telegram.org/bot1234567890:ABCdefGHIjklMNOpqrsTUVwxyz/setWebhook?url=https://yourapp.replit.app/webhook
```

You should see:
```json
{"ok":true,"result":true,"description":"Webhook was set"}
```

### 4.2 Verify Webhook

Check it's working:
```
https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getWebhookInfo
```

Should show:
```json
{
  "ok": true,
  "result": {
    "url": "https://yourapp.replit.app/webhook",
    "pending_update_count": 0
  }
}
```

### 4.3 Set WebApp URL in BotFather

1. Go back to BotFather
2. Send `/myapps`
3. Select your bot
4. Click "Edit App"
5. Set "Web App URL" to your Replit URL: `https://yourapp.replit.app`

**OR**

Send `/setmenubutton` to BotFather:
- Select your bot
- Send your Replit URL
- Send button text: "🤝 Open Vouch Portal"

---

## Step 5: Test Your Bot! 🎉

### 5.1 Test Basic Commands

1. Open your bot on Telegram
2. Send `/start`
3. You should get a welcome message with a button

### 5.2 Open the WebApp

1. Click "Open Vouch Portal" button
2. The WebApp should load with your profile
3. Try navigating between tabs

### 5.3 Test Vouching

1. Invite a friend to your bot
2. Both use `/start`
3. Try vouching for each other using the WebApp

---

## Troubleshooting

### Bot doesn't respond
- ✅ Check webhook is set correctly (`/getWebhookInfo`)
- ✅ Check Replit app is running (green dot)
- ✅ Check logs in Replit console for errors
- ✅ Verify BOT_TOKEN is correct

### WebApp doesn't load
- ✅ Check WEBHOOK_URL is your Replit URL
- ✅ Make sure `webapp` folder exists with `index.html`
- ✅ Check browser console for errors (F12)
- ✅ Try clearing browser cache

### Database errors
- ✅ Check DATABASE_URL is correct
- ✅ Test database connection separately
- ✅ Ensure database allows connections from Replit IP
- ✅ Check Replit logs for specific error messages

### "User not found" errors
- ✅ Make sure user sent `/start` to bot first
- ✅ Check database has user record
- ✅ Wait a few seconds and try again

---

## Next Steps

### Customize Your Bot

**Change Colors:**
Edit `webapp/static/styles.css` - see `:root` variables

**Adjust Ranks:**
Edit `database.py` - see `calculate_rank()` function

**Add Features:**
- Extend database schema
- Add new API endpoints
- Create new bot commands

### Launch to Your Community

1. Share bot link: `https://t.me/YourBotUsername`
2. Post in your Telegram group
3. Encourage members to vouch for each other
4. Monitor analytics with `/stats` command

### Keep It Running 24/7

**Free option:**
- Replit's "Always On" is available on paid plans

**Alternatives:**
- Use [UptimeRobot](https://uptimerobot.com) to ping your app every 5 minutes
- Deploy to Railway, Render, or DigitalOcean for always-on hosting

---

## Admin Features

As the admin (your ADMIN_ID), you can:

- Use `/stats` command to see analytics
- Access "Insights" tab in WebApp
- View all users and vouches
- Monitor system health

---

## Need Help?

1. Check the [README.md](README.md) for detailed documentation
2. Review error logs in Replit console
3. Test each component separately:
   - Database connection
   - Bot webhook
   - WebApp loading
   - API endpoints

---

## Security Checklist

- ✅ BOT_TOKEN is secret (never share!)
- ✅ ADMIN_ID is correct (only you)
- ✅ Database credentials are secure
- ✅ Webhook URL is HTTPS
- ✅ Content filtering is enabled

---

**Congratulations! Your Vouch Portal is now live! 🎉**

Start building trust in your community today!
