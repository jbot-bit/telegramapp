# ✅ Deployment Checklist - Vouch Portal

Use this checklist to ensure a smooth deployment.

## Pre-Deployment (Setup)

### 1. Telegram Bot Setup
- [ ] Created bot via @BotFather
- [ ] Saved BOT_TOKEN securely
- [ ] Set bot description
- [ ] Set bot about text
- [ ] Set bot commands
- [ ] Obtained ADMIN_ID from @userinfobot
- [ ] Noted BOT_USERNAME (without @)

### 2. Database Setup
- [ ] Created PostgreSQL database (Replit/Supabase/Neon)
- [ ] Saved DATABASE_URL connection string
- [ ] Tested database connection
- [ ] Database accepts remote connections

### 3. Code Validation
- [ ] Ran `python validate_structure.py`
- [ ] All files present and valid
- [ ] No syntax errors in Python files

## Deployment (Replit)

### 4. Replit Setup
- [ ] Created Replit account
- [ ] Created new Repl (Python)
- [ ] Uploaded all project files OR imported from GitHub
- [ ] Files are in correct structure

### 5. Environment Variables (Secrets)
Configure in Replit Secrets panel:

- [ ] `BOT_TOKEN` = Your bot token
- [ ] `BOT_USERNAME` = Your bot username (no @)
- [ ] `WEBHOOK_URL` = Your Replit URL (get after first run)
- [ ] `ADMIN_ID` = Your Telegram user ID
- [ ] `DATABASE_URL` = PostgreSQL connection string
- [ ] `PORT` = 8080 (optional)

### 6. Initial Deployment
- [ ] Clicked "Run" button
- [ ] Dependencies installed successfully
- [ ] Server started without errors
- [ ] Copied Replit URL (e.g., `https://yourapp.replit.app`)
- [ ] Added URL to `WEBHOOK_URL` secret
- [ ] Restarted the app

## Post-Deployment (Configuration)

### 7. Webhook Setup
- [ ] Opened webhook setup URL in browser:
  ```
  https://api.telegram.org/bot<BOT_TOKEN>/setWebhook?url=<WEBHOOK_URL>/webhook
  ```
- [ ] Got response: `{"ok":true,"result":true}`
- [ ] Verified webhook with getWebhookInfo:
  ```
  https://api.telegram.org/bot<BOT_TOKEN>/getWebhookInfo
  ```
- [ ] Confirmed `url` matches your webhook URL
- [ ] Confirmed `pending_update_count` is 0

### 8. BotFather WebApp Configuration
**Option A: Menu Button**
- [ ] Sent `/setmenubutton` to @BotFather
- [ ] Selected your bot
- [ ] Sent your Replit URL
- [ ] Set button text: "🤝 Open Vouch Portal"

**Option B: Web App** (if available)
- [ ] Sent `/myapps` to @BotFather
- [ ] Created or edited app
- [ ] Set Web App URL to Replit URL

## Testing

### 9. Bot Commands Test
- [ ] Opened your bot on Telegram
- [ ] Sent `/start` → Got welcome message
- [ ] Sent `/profile` → Got profile info
- [ ] Sent `/help` → Got help message
- [ ] Sent `/leaderboard` → Got leaderboard
- [ ] (Admin only) Sent `/stats` → Got analytics

### 10. WebApp Test
- [ ] Clicked "Open Vouch Portal" button
- [ ] WebApp loaded successfully
- [ ] Profile tab shows correct data
- [ ] Navigation between tabs works
- [ ] Search functionality works
- [ ] No JavaScript errors in console (F12)

### 11. Vouching Flow Test
- [ ] Invited a test user to bot
- [ ] Test user sent `/start`
- [ ] Tried vouching for test user
- [ ] Vouch was recorded
- [ ] Vouch appears in profile
- [ ] Rank updated correctly (if threshold reached)

### 12. Viral Features Test
- [ ] Clicked "Request Vouch" button
- [ ] Share dialog opened
- [ ] Referral link contains correct format
- [ ] Tested referral link (opens bot with payload)
- [ ] Share profile works
- [ ] Share text includes correct bot username

### 13. Admin Features Test (If Admin)
- [ ] Insights tab is visible in WebApp
- [ ] Analytics data loads correctly
- [ ] Top helpers shown
- [ ] Rank distribution displayed
- [ ] `/stats` command works

## Production Checks

### 14. Performance
- [ ] Page loads in <2 seconds
- [ ] API responses <500ms
- [ ] No console errors
- [ ] Mobile responsive works
- [ ] Dark theme displays correctly

### 15. Security
- [ ] BOT_TOKEN is secret (not in code)
- [ ] DATABASE_URL is secret (not in code)
- [ ] ADMIN_ID is correct
- [ ] Content filtering works (tested banned words)
- [ ] Rate limiting active (tried multiple invites)

### 16. Error Handling
- [ ] Tested invalid username in vouch form
- [ ] Tested vouching for self (should fail)
- [ ] Tested duplicate vouch (should fail)
- [ ] Tested empty form submission
- [ ] All errors show user-friendly messages

### 17. Database
- [ ] Database schema created automatically
- [ ] Tables exist (users, vouches, events, etc.)
- [ ] Data persists after restart
- [ ] No connection timeout errors

### 18. Monitoring
- [ ] `/health` endpoint responds
- [ ] Replit logs show no errors
- [ ] Database queries are fast
- [ ] No memory leaks (check Replit metrics)

## Launch

### 19. Community Announcement
- [ ] Prepared announcement message
- [ ] Posted bot link in community
- [ ] Explained how it works
- [ ] Shared example use case
- [ ] Answered initial questions

### 20. Post-Launch Monitoring
- [ ] Checked logs every hour (first day)
- [ ] Monitored error rate
- [ ] Watched user signups
- [ ] Responded to user feedback
- [ ] Checked `/stats` daily

## Maintenance

### 21. Regular Tasks
- [ ] Check logs weekly
- [ ] Review analytics monthly
- [ ] Update dependencies quarterly
- [ ] Backup database monthly
- [ ] Monitor costs

### 22. Scaling Considerations
- [ ] Monitor active users
- [ ] Check database size
- [ ] Consider upgrading Replit plan if needed
- [ ] Add always-on feature (paid plan)
- [ ] Consider CDN for static assets at scale

## Troubleshooting

### If Bot Doesn't Respond
1. Check webhook is set correctly
2. Check Replit app is running
3. Check BOT_TOKEN is correct
4. Review Replit logs for errors
5. Test `/health` endpoint

### If WebApp Doesn't Load
1. Check WEBHOOK_URL is correct
2. Check static files exist in `webapp/`
3. Check browser console (F12) for errors
4. Test direct URL in browser
5. Check CORS settings

### If Database Errors
1. Check DATABASE_URL is correct
2. Test database connection separately
3. Check database server is online
4. Review connection limits
5. Check table creation logs

### If Vouches Don't Work
1. Check both users have profiles
2. Check vouch isn't duplicate
3. Check database write permissions
4. Review API endpoint logs
5. Test with admin account

## Success Criteria

Your deployment is successful when:
- ✅ Bot responds to all commands
- ✅ WebApp loads on mobile
- ✅ Vouching creates records
- ✅ Ranks update automatically
- ✅ Analytics track events
- ✅ No errors in logs
- ✅ Users can navigate all tabs
- ✅ Share/invite features work

## Next Steps After Launch

1. **Week 1:** Monitor closely, fix any issues
2. **Week 2:** Gather user feedback, make improvements
3. **Month 1:** Review analytics, adjust features
4. **Ongoing:** Maintain, update, scale as needed

## Support Resources

- 📖 [README.md](README.md) - Technical documentation
- 🚀 [SETUP_GUIDE.md](SETUP_GUIDE.md) - Detailed setup
- 📊 [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) - Feature overview
- 🔍 [validate_structure.py](validate_structure.py) - Structure validator

## Emergency Contacts

- Replit Status: https://status.replit.com
- Telegram Status: https://telegram.org/status
- Database Provider Status: (your provider's status page)

---

**🎉 Congratulations on your deployment!**

Remember to check all boxes before considering deployment complete.

_Last updated: 2025-10-30_
