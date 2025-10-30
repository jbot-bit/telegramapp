# Vouch Portal Bot Setup Guide

## Quick Setup in BotFather

### 1. Configure Menu Button (MOST IMPORTANT)
Open @BotFather in Telegram and send these commands:

```
/mybots
Select: @vouchadminbot
Click: Bot Settings → Menu Button
Set URL: https://telegramapp11.replit.app
Set Button Text: Open Vouch Portal
```

### 2. Update Bot Description
```
/setdescription
@vouchadminbot
Build trust through community vouches. Get verified by your peers and unlock your reputation.
```

### 3. Set Bot Commands
```
/setcommands
@vouchadminbot
start - Open Vouch Portal
help - Get help
share - Share your profile
```

## How Users Access Your App

### Method 1: Direct Bot Link (Recommended)
Share this link: `https://t.me/vouchadminbot`
- Users click the link
- Press START or the menu button
- App opens instantly

### Method 2: App Link (After Menu Button Setup)
Share this link: `https://t.me/vouchadminbot/app`
- Opens app directly in Telegram
- No START command needed

### Method 3: Profile Share Links
Share specific profiles: `https://t.me/vouchadminbot?start=profile_123456`
- Replace 123456 with actual Telegram user ID
- Opens directly to that user's profile

### Method 4: Referral Links
Track referrals: `https://t.me/vouchadminbot?start=ref_123456`
- Replace 123456 with referrer's ID
- Tracks who invited whom

## Testing Your Setup

1. Open @vouchadminbot
2. You should see a menu button at the bottom
3. Click it to open the app directly
4. Or use /start for the welcome message

## Troubleshooting

**Users get "Telegram Required" error:**
- They're not opening through Telegram
- Share the bot link, not the website URL

**App doesn't open:**
- Check menu button is configured
- Verify WEBHOOK_URL environment variable is set correctly

**Profile 404 errors:**
- Users need to refresh/reopen the app
- Cache has been cleared with version parameters