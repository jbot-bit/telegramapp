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
    """Handle /start command - streamlined for quick access"""
    user = update.effective_user
    chat_id = update.effective_chat.id

    # Parse deep link parameters
    referrer_id = None
    direct_to_profile = None
    
    if context.args:
        arg = context.args[0]
        if arg.startswith("ref_"):
            try:
                referrer_id = int(arg.replace("ref_", ""))
            except ValueError:
                pass
        elif arg.startswith("profile_"):
            try:
                direct_to_profile = int(arg.replace("profile_", ""))
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

    # Determine webapp URL
    if direct_to_profile:
        webapp_url = f"{WEBHOOK_URL}?view=profile&id={direct_to_profile}"
        button_text = "👀 View Profile"
        message_intro = f"**Check out this profile!**\n\n"
    else:
        webapp_url = WEBHOOK_URL
        button_text = "🚀 Open App"
        message_intro = ""

    # Single button to open app
    keyboard = [[InlineKeyboardButton(button_text, web_app=WebAppInfo(url=webapp_url))]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Simplified welcome message
    if user_data['total_vouches'] == 0:
        status_message = "🆕 **New Member** - Get your first vouch!"
    else:
        status_message = f"{rank_emoji} **{rank_name}** • {user_data['total_vouches']} vouches"

    welcome_message = f"""
{message_intro}**Vouch Portal** 🤝

{status_message}

{button_text} to start building trust!
"""

    await update.message.reply_text(
        welcome_message.strip(),
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

    # Create vouch (works for both existing and non-existing users)
    result = await db.create_vouch(user.id, to_username=target_username, message=message)

    if "error" in result:
        await update.message.reply_text(f"❌ {result['error']}")
        return

    # Check if this was a pending vouch or immediate vouch
    if result.get("is_pending"):
        # Pending vouch for user who hasn't joined yet
        await update.message.reply_text(
            f"✅ Vouch recorded for @{target_username}!\n\n"
            f"They haven't used the bot yet, but your vouch will be counted when they join.",
            parse_mode="Markdown"
        )
    else:
        # Immediate vouch for existing user
        target_user_id = result.get("to_user_id")
        
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

            # NOTIFICATIONS DISABLED - No rank-up messages sent
            # Users will see rank updates when they open the app
            pass


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


async def share_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get shareable profile link"""
    user = update.effective_user
    
    # Get user data to show their stats
    user_data = await db.get_user(user.id)
    
    # Create shareable link
    share_link = f"https://t.me/{BOT_USERNAME}?start=profile_{user.id}"
    
    # Create webapp button
    webapp_url = WEBHOOK_URL
    keyboard = [[
        InlineKeyboardButton("👀 View My Profile", web_app=WebAppInfo(url=webapp_url))
    ]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if user_data:
        rank_emoji = db.get_rank_emoji(user_data["rank"])
        share_text = f"""
**Your Profile Link:**
`{share_link}`

{rank_emoji} You have **{user_data['total_vouches']}** vouches

Tap to copy the link above 👆
Share it to let others vouch for you!
"""
    else:
        share_text = f"""
**Your Profile Link:**
`{share_link}`

Share this link to start receiving vouches!

Tap to copy the link above 👆
"""
    
    await update.message.reply_text(
        share_text.strip(),
        reply_markup=reply_markup,
        parse_mode="Markdown"
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
    application.add_handler(CommandHandler("share", share_command))

    # Callback query handler
    application.add_handler(CallbackQueryHandler(callback_query_handler))

    # New member handler (for groups)
    application.add_handler(MessageHandler(
        filters.StatusUpdate.NEW_CHAT_MEMBERS,
        group_new_member_handler
    ))

    logger.info("Bot handlers setup complete")


async def get_user_profile_photo_file_id(user_id: int) -> Optional[str]:
    """
    Fetch user's profile photo file_id from Telegram
    Returns the file_id (NOT a URL) or None if no photo available
    """
    try:
        from telegram import Bot
        bot = Bot(token=BOT_TOKEN)
        
        # Get user profile photos
        photos = await bot.get_user_profile_photos(user_id, limit=1)
        
        if photos.total_count > 0:
            # Get the first photo (most recent) - return file_id only
            file_id = photos.photos[0][0].file_id
            
            logger.info(f"Fetched profile photo file_id for user {user_id}")
            return file_id
        else:
            logger.info(f"No profile photo found for user {user_id}")
            return None
            
    except Exception as e:
        logger.error(f"Error fetching profile photo for user {user_id}: {e}")
        return None


async def download_profile_photo_bytes(file_id: str) -> Optional[bytes]:
    """
    Download profile photo bytes from Telegram using file_id
    Returns the photo bytes or None if download fails
    """
    try:
        from telegram import Bot
        bot = Bot(token=BOT_TOKEN)
        
        # Get file info
        file_info = await bot.get_file(file_id)
        
        # Download the file bytes
        photo_bytes = await file_info.download_as_bytearray()
        
        logger.info(f"Downloaded profile photo for file_id {file_id}")
        return bytes(photo_bytes)
            
    except Exception as e:
        logger.error(f"Error downloading profile photo for file_id {file_id}: {e}")
        return None


def create_bot_application() -> Application:
    """Create and configure the bot application"""
    application = Application.builder().token(BOT_TOKEN).build()
    setup_bot_handlers(application)
    return application
