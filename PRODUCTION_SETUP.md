# Production Environment Setup Guide

This guide explains how to properly configure and separate your development and production environments for the Vouch Portal application on Replit.

## Understanding Development vs Production

### Development Environment
- **Purpose**: Testing, feature development, and experimentation
- **Database**: Replit development database (separate instance)
- **Access**: Workspace webview and database tools
- **Features**: Hot-reload, debugging tools, agent access
- **Environment Variable**: `REPLIT_ENVIRONMENT=development` (automatic)

### Production Environment
- **Purpose**: Serving real users with stable, optimized code
- **Database**: Production database (separate instance, managed via Publishing)
- **Access**: Published URL (e.g., https://yourapp.replit.app)
- **Features**: Autoscale, no reload, optimized for stability
- **Environment Variable**: `REPLIT_ENVIRONMENT=production` (automatic)

## Key Differences

| Aspect | Development | Production |
|--------|-------------|------------|
| Database | Dev database (agent can modify) | Prod database (manual control only) |
| Secrets | Replit Secrets panel | Publishing > Secrets |
| Hot Reload | Enabled | Disabled |
| Access | Workspace only | Public URL |
| Scaling | Single instance | Autoscale based on traffic |
| Monitoring | Workspace logs | Publishing logs |

## Environment Separation Safeguards

### Database Isolation
1. **Development database** is completely separate from production
2. Agent and database tools can ONLY modify development database
3. Production database is never touched by agent or development tools
4. Schema changes are NOT automatically applied to production

### Environment Variables
1. **Development secrets**: Set in Replit Secrets panel (left sidebar)
2. **Production secrets**: Set in Publishing tool > Secrets tab
3. Must configure secrets separately for each environment

### Code Behavior
The application automatically detects which environment it's running in:

```python
is_production = os.getenv("REPLIT_ENVIRONMENT", "development") == "production"

# Development: reload=True (hot-reload enabled)
# Production: reload=False (stable, no reload)
uvicorn.run("main:app", host="0.0.0.0", port=port, reload=not is_production)
```

## Setting Up Production

### Step 1: Configure Production Secrets

1. Click the "Publish" button in your Replit workspace
2. Navigate to the "Secrets" tab in the Publishing tool
3. Add the following environment variables:

```
BOT_TOKEN=<your_production_bot_token>
BOT_USERNAME=<your_bot_username>
WEBHOOK_URL=<your_published_url>
ADMIN_ID=<your_telegram_user_id>
DATABASE_URL=<production_database_url>
```

**Important**: 
- Use different `BOT_TOKEN` for production (recommended for safety)
- `WEBHOOK_URL` should be your published Replit URL
- `DATABASE_URL` should point to your production database (NOT the dev database)

### Step 2: Production Database Setup

**Option A: Replit Production Database**
1. In Publishing tool, go to Database tab
2. Enable the production database
3. Connection string is automatically available as `DATABASE_URL`

**Option B: External Database (Supabase/Neon)**
1. Create a NEW database for production (separate from development)
2. Get the connection string
3. Add it to Publishing > Secrets as `DATABASE_URL`

### Step 3: Deploy Configuration

The deployment is already configured in `.replit`:

```toml
[deployment]
run = ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5000"]
deploymentTarget = "autoscale"
```

- **Autoscale**: Automatically scales based on traffic
- **No reload**: Production runs stable code without hot-reload
- **Port 5000**: Standard Replit port

### Step 4: Publish Your App

1. Click "Publish" in your workspace
2. Review the configuration
3. Set machine power (compute units) as needed
4. Set max machines for autoscaling
5. Click "Publish" to deploy

### Step 5: Test Production Environment

After publishing:

1. Visit your published URL
2. Test all bot commands (`/start`, `/profile`, etc.)
3. Test the WebApp interface
4. Verify database connections work
5. Check that webhook is properly configured
6. Monitor logs in Publishing > Logs

## Database Migration Strategy

When you make schema changes in development:

1. **Test thoroughly** in development environment first
2. **Review changes**: Check what tables/columns changed
3. **Backup production**: Always backup before schema changes
4. **Apply manually**: Use database tools to apply schema changes to production
5. **Never assume**: Changes don't automatically propagate to production

### Safe Migration Process

```bash
# 1. Test in development
# Make changes, test thoroughly

# 2. Document changes
# List all schema modifications

# 3. Apply to production
# Use database admin panel or SQL client
# Run schema changes manually

# 4. Republish if needed
# If code changes require new schema
```

## Environment Variable Checklist

### Development (Replit Secrets Panel)
- [ ] `BOT_TOKEN` - Development bot token
- [ ] `BOT_USERNAME` - Bot username (same for both)
- [ ] `WEBHOOK_URL` - Replit dev URL (e.g., https://project.username.repl.co)
- [ ] `ADMIN_ID` - Your Telegram user ID
- [ ] `DATABASE_URL` - Development database URL

### Production (Publishing > Secrets)
- [ ] `BOT_TOKEN` - Production bot token (can be same or different)
- [ ] `BOT_USERNAME` - Bot username (same as development)
- [ ] `WEBHOOK_URL` - Published URL (e.g., https://yourapp.replit.app)
- [ ] `ADMIN_ID` - Your Telegram user ID
- [ ] `DATABASE_URL` - Production database URL (MUST be different from dev)

## Monitoring Production

### Health Check
Visit: `https://yourapp.replit.app/health`

Expected response:
```json
{
  "status": "healthy",
  "service": "vouch-portal",
  "database": "connected"
}
```

### Logs
- Access via Publishing > Logs tab
- Monitor for errors and warnings
- Check database connection status
- Review API response times

### Metrics
- Active users (DAU/MAU)
- Vouch creation rate
- API response times
- Database query performance

## Troubleshooting

### Production App Not Starting
1. Check Publishing > Logs for errors
2. Verify all secrets are set correctly
3. Ensure `DATABASE_URL` is valid
4. Test database connection separately

### Database Connection Issues
1. Verify production `DATABASE_URL` is correct
2. Check database server is online
3. Ensure connection limits aren't exceeded
4. Review SSL/TLS requirements

### Environment Variable Issues
1. Double-check secrets in Publishing tool
2. Ensure no typos in variable names
3. Verify `WEBHOOK_URL` matches published URL
4. Confirm `BOT_TOKEN` is valid

### Bot Not Responding in Production
1. Check webhook is set to production URL:
   ```
   https://api.telegram.org/bot<BOT_TOKEN>/setWebhook?url=<WEBHOOK_URL>/webhook
   ```
2. Verify `BOT_TOKEN` matches the one used for webhook
3. Check Publishing logs for webhook errors
4. Test `/health` endpoint

## Security Best Practices

1. **Never commit secrets** to version control
2. **Use different bot tokens** for dev and prod (recommended)
3. **Separate databases** completely
4. **Review logs regularly** for suspicious activity
5. **Backup production database** before major changes
6. **Test in development** before deploying to production
7. **Monitor access logs** for unusual patterns

## Deployment Workflow

### For New Features
1. Develop and test in workspace (development environment)
2. Test with development database
3. Verify functionality works correctly
4. Review any database schema changes
5. Update production database schema if needed
6. Republish via Publishing tool
7. Test on production URL
8. Monitor logs for issues

### For Bug Fixes
1. Reproduce in development
2. Fix and test in development
3. Verify fix works
4. Republish to production
5. Verify fix in production
6. Monitor for any side effects

### For Database Changes
1. Make changes in development database
2. Test thoroughly with new schema
3. Document all changes
4. Backup production database
5. Apply schema changes to production manually
6. Test production database
7. Republish application
8. Verify everything works

## Summary

The key principle is: **Development and production are completely separate environments**

- Separate databases (development vs production)
- Separate secrets configuration
- Separate access controls
- Separate monitoring and logs
- Manual control over production changes
- Automatic environment detection via `REPLIT_ENVIRONMENT`

This ensures you can safely develop and test features without affecting real users or production data.

## Support

For issues:
- Development problems: Use workspace debugging tools
- Production problems: Check Publishing > Logs
- Database issues: Use database admin panels
- Telegram issues: Check webhook configuration

For help:
- Replit Status: https://status.replit.com
- Telegram Bot API: https://core.telegram.org/bots/api
- Replit Docs: https://docs.replit.com

---

Last updated: 2025-10-30
