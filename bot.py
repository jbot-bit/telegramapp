"""
Telegram Bot handlers for Vouch Portal
Handles all bot commands and interactions
"""
import os
import logging
import re
from typing import Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters
)
from database import db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Bot configuration
BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
BOT_USERNAME = os.getenv("BOT_USERNAME", "VouchPortalBot")

# Banned words for content filtering
BANNED_WORDS = [
    "scam", "fraud", "fake", "cheat", "steal", "hack",
    "phishing", "ponzi", "pyramid"
]

def sanitize_message(text: str) -> str:
    """Remove or replace banned words in user messages"""
    if not text:
        return ""

    sanitized = text
    for word in BANNED_WORDS:
        pattern = re.compile(re.escape(word), re.IGNORECASE)
        sanitized = pattern.sub("[redacted]", sanitized)

    return sanitized[:120]  # Limit to 120 characters


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    user = update.effective_user
    chat_id = update.effective_chat.id

    # Parse referral code from deep link
    referrer_id = None
    if context.args:
        arg = context.args[0]
        if arg.startswith("ref_"):
            try:
                referrer_id = int(arg.replace("ref_", ""))
            except ValueError:
                pass
        elif arg.startswith("profile_"):
            # Direct to profile view
            try:
                profile_id = int(arg.replace("profile_", ""))
                webapp_url = f"{WEBHOOK_URL}?view=profile&id={profile_id}"
                keyboard = [[InlineKeyboardButton("Open Profile", web_app=WebAppInfo(url=webapp_url))]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await update.message.reply_text(
                    f"👋 View this user's profile:",
                    reply_markup=reply_markup
                )
                return
            except ValueError:
                pass

    # Create or get user
    user_data = await db.get_or_create_user(
        telegram_user_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        referrer_id=referrer_id
    )

    # Log referral if applicable
    if referrer_id:
        await db.log_event("referral_signup", user.id, {"referrer_id": referrer_id})

    # Get user's current stats
    rank_emoji = db.get_rank_emoji(user_data["rank"])
    rank_name = db.get_rank_name(user_data["rank"])

    # Create webapp button
    webapp_url = WEBHOOK_URL
    keyboard = [[InlineKeyboardButton("🤝 Open Vouch Portal", web_app=WebAppInfo(url=webapp_url))]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    welcome_message = f"""
👋 Welcome to **Vouch Portal**, {user.first_name}!

Your current status:
{rank_emoji} **{rank_name}**
Vouches received: **{user_data['total_vouches']}**

Build trust through community vouches. Tap below to get started!

_Community opinions only. Be respectful._
"""

    await update.message.reply_text(
        welcome_message,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )


async def profile_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /profile command"""
    user = update.effective_user

    # Get user data
    user_data = await db.get_user(user.id)
    if not user_data:
        await update.message.reply_text("Please use /start first to create your profile.")
        return

    # Get vouches
    vouches = await db.get_vouches_for_user(user.id)

    rank_emoji = db.get_rank_emoji(user_data["rank"])
    rank_name = db.get_rank_name(user_data["rank"])

    # Create webapp button
    webapp_url = f"{WEBHOOK_URL}?view=profile&id={user.id}"
    keyboard = [[InlineKeyboardButton("📊 View Full Profile", web_app=WebAppInfo(url=webapp_url))]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    profile_text = f"""
**Your Profile**

{rank_emoji} **{rank_name}**
Total Vouches: **{user_data['total_vouches']}**
Member since: {user_data['first_seen_at'].strftime('%B %d, %Y')}

Recent vouches: **{len(vouches[:5])}** shown
"""

    await update.message.reply_text(
        profile_text,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )


async def vouch_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /vouch command"""
    user = update.effective_user

    if not context.args:
        await update.message.reply_text(
            "Usage: `/vouch @username [optional message]`\n\n"
            "Or use the WebApp for an easier experience!",
            parse_mode="Markdown"
        )
        return

    # Parse target username
    target_username = context.args[0].replace("@", "")
    message = " ".join(context.args[1:]) if len(context.args) > 1 else None

    # Sanitize message
    if message:
        message = sanitize_message(message)

    # Get target user by username
    target_user = await db.pool.fetchrow(
        "SELECT telegram_user_id FROM users WHERE username = $1",
        target_username
    )

    if not target_user:
        await update.message.reply_text(
            f"User @{target_username} not found. They need to use /start first."
        )
        return

    target_user_id = target_user["telegram_user_id"]

    if target_user_id == user.id:
        await update.message.reply_text("You cannot vouch for yourself!")
        return

    # Create vouch
    result = await db.create_vouch(user.id, target_user_id, message)

    if "error" in result:
        await update.message.reply_text(f"❌ {result['error']}")
        return

    # Get updated user data
    target_data = await db.get_user(target_user_id)
    rank_emoji = db.get_rank_emoji(target_data["rank"])

    await update.message.reply_text(
        f"✅ Vouch recorded for @{target_username}!\n\n"
        f"They now have {rank_emoji} **{target_data['total_vouches']}** vouches.",
        parse_mode="Markdown"
    )

    # Check if this triggered a rank up
    rank_events = await db.pool.fetch(
        "SELECT * FROM rank_events WHERE user_id = $1 ORDER BY created_at DESC LIMIT 1",
        target_user_id
    )

    if rank_events and (rank_events[0]["created_at"]).timestamp() > (result["created_at"]).timestamp() - 5:
        # Rank up just happened
        new_rank_name = db.get_rank_name(target_data["rank"])
        new_rank_emoji = db.get_rank_emoji(target_data["rank"])

        # Send notification to target user
        try:
            webapp_url = f"{WEBHOOK_URL}?view=profile&id={target_user_id}"
            keyboard = [[
                InlineKeyboardButton("🎉 View My Profile", web_app=WebAppInfo(url=webapp_url)),
                InlineKeyboardButton("Share Achievement", switch_inline_query=f"I just reached {new_rank_emoji} {new_rank_name} on Vouch Portal!")
            ]]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await context.bot.send_message(
                chat_id=target_user_id,
                text=f"🎉 **Congratulations!**\n\nYou've been promoted to {new_rank_emoji} **{new_rank_name}**!\n\nYour trust score just increased.",
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Failed to send rank-up notification: {e}")


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /stats command (admin only)"""
    user = update.effective_user

    if user.id != ADMIN_ID:
        await update.message.reply_text("This command is only available to admins.")
        return

    # Get analytics
    analytics = await db.get_analytics_summary()

    stats_text = f"""
**📊 Vouch Portal Statistics**

**Users:**
• Total: {analytics['total_users']}
• Active (24h): {analytics['active_users']['24h']}
• Active (7d): {analytics['active_users']['7d']}
• New (7d): {analytics['new_signups_7d']}

**Engagement:**
• Total Vouches: {analytics['total_vouches']}
• Mutual Vouches: {analytics['mutual_vouch_count']}

**Top Helpers (This Week):**
"""

    for helper in analytics['top_helpers'][:5]:
        username = helper['username'] or helper['first_name']
        stats_text += f"• @{username}: {helper['vouch_count']} vouches\n"

    stats_text += "\n**Rank Distribution:**\n"
    for rank_data in analytics['rank_distribution']:
        emoji = db.get_rank_emoji(rank_data['rank'])
        rank_name = db.get_rank_name(rank_data['rank'])
        stats_text += f"• {emoji} {rank_name}: {rank_data['count']}\n"

    # Create dashboard button
    webapp_url = f"{WEBHOOK_URL}?view=admin"
    keyboard = [[InlineKeyboardButton("📈 Open Full Dashboard", web_app=WebAppInfo(url=webapp_url))]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        stats_text,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )


async def leaderboard_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /leaderboard command"""
    analytics = await db.get_analytics_summary()

    leaderboard_text = "**🏆 Top Vouched Users**\n\n"

    for i, user in enumerate(analytics['most_vouched'][:10], 1):
        username = user['username'] or user['first_name']
        emoji = db.get_rank_emoji(user['rank'])
        leaderboard_text += f"{i}. @{username} {emoji} — {user['total_vouches']} vouches\n"

    leaderboard_text += "\n_Build your reputation through community trust!_"

    # Create webapp button
    webapp_url = f"{WEBHOOK_URL}?view=community"
    keyboard = [[InlineKeyboardButton("👥 View Community", web_app=WebAppInfo(url=webapp_url))]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        leaderboard_text,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    help_text = """
**🤝 Vouch Portal Commands**

/start — Initialize your profile
/profile — View your stats
/vouch @username [message] — Vouch for someone
/leaderboard — See top users
/help — Show this message

**About Vouch Portal:**
Build trust through community vouches. Your reputation grows as people verify you.

**Ranks:**
🚫 Unverified (0-2)
✅ Verified (3-5)
🔷 Trusted (6-10)
🛡 Endorsed (11-15)
👑 Top-Tier (16+)

_All feedback is community-based. Keep it respectful!_
"""

    # Create webapp button
    webapp_url = WEBHOOK_URL
    keyboard = [[InlineKeyboardButton("🚀 Open WebApp", web_app=WebAppInfo(url=webapp_url))]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        help_text,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )


async def callback_query_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle callback queries from inline buttons"""
    query = update.callback_query
    await query.answer()

    data = query.data

    if data.startswith("vouch_"):
        # Handle vouch button (from group posts)
        parts = data.split("_")
        if len(parts) != 3:
            return

        action = parts[1]  # yes or unsure
        target_user_id = int(parts[2])
        from_user_id = query.from_user.id

        if action == "yes":
            # Create vouch
            result = await db.create_vouch(from_user_id, target_user_id)

            if "error" in result:
                await query.answer(f"❌ {result['error']}", show_alert=True)
                return

            await query.answer("✅ Vouch recorded!", show_alert=False)

            # Update message
            target_data = await db.get_user(target_user_id)
            rank_emoji = db.get_rank_emoji(target_data["rank"])

            await query.edit_message_text(
                f"✅ Vouch received!\n\n"
                f"User now has {rank_emoji} **{target_data['total_vouches']}** vouches.",
                parse_mode="Markdown"
            )

        elif action == "unsure":
            await query.answer("👍 Thanks for your feedback", show_alert=False)


async def group_new_member_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle new members joining the group"""
    for member in update.message.new_chat_members:
        if member.is_bot:
            continue

        # Create user profile
        await db.get_or_create_user(
            telegram_user_id=member.id,
            username=member.username,
            first_name=member.first_name,
            last_name=member.last_name
        )

        # Send vouch request to group
        keyboard = [
            [
                InlineKeyboardButton("👍 Yes", callback_data=f"vouch_yes_{member.id}"),
                InlineKeyboardButton("⚠️ Unsure", callback_data=f"vouch_unsure_{member.id}")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            f"🧾 @{member.username or member.first_name} joined. Do you vouch for them?",
            reply_markup=reply_markup
        )


def setup_bot_handlers(application: Application):
    """Setup all bot command handlers"""
    # Command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("profile", profile_command))
    application.add_handler(CommandHandler("vouch", vouch_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CommandHandler("leaderboard", leaderboard_command))
    application.add_handler(CommandHandler("help", help_command))

    # Callback query handler
    application.add_handler(CallbackQueryHandler(callback_query_handler))

    # New member handler (for groups)
    application.add_handler(MessageHandler(
        filters.StatusUpdate.NEW_CHAT_MEMBERS,
        group_new_member_handler
    ))

    logger.info("Bot handlers setup complete")


def create_bot_application() -> Application:
    """Create and configure the bot application"""
    application = Application.builder().token(BOT_TOKEN).build()
    setup_bot_handlers(application)
    return application
