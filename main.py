"""
FastAPI main application for Vouch Portal
Handles webhook, API endpoints, and serves the WebApp
"""
import os
import logging
from contextlib import asynccontextmanager
from typing import Optional
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from telegram import Update
from bot import create_bot_application, sanitize_message
from database import db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

# Global bot application
bot_app = None


def sanitize_user_profile_url(user_dict):
    """
    Sanitize profile_picture_url to prevent bot token leaks.
    If the URL contains api.telegram.org or http/https, clear it (unsafe URL).
    Safe values are Telegram file_ids which will be proxied.
    """
    if user_dict and "profile_picture_url" in user_dict:
        url = user_dict.get("profile_picture_url")
        if url and ("api.telegram.org" in url.lower() or "http://" in url.lower() or "https://" in url.lower()):
            logger.warning(f"Sanitized unsafe URL for user {user_dict.get('telegram_user_id')}: {url[:50]}")
            user_dict["profile_picture_url"] = None
    return user_dict


def sanitize_response_data(data):
    """
    Recursively sanitize all user dictionaries in a response to prevent token leaks.
    This is applied to all JSON responses as a safety net.
    """
    if isinstance(data, dict):
        # Check if this looks like a user dict
        if "profile_picture_url" in data:
            sanitize_user_profile_url(data)
        # Recursively sanitize all nested dicts
        for key, value in data.items():
            data[key] = sanitize_response_data(value)
    elif isinstance(data, list):
        # Sanitize all items in list
        return [sanitize_response_data(item) for item in data]
    return data


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for FastAPI app"""
    global bot_app

    # Startup
    logger.info("Starting Vouch Portal application...")

    # Connect to database
    await db.connect()

    # Initialize bot (allow app to start even if bot fails)
    try:
        bot_app = create_bot_application()
        await bot_app.initialize()
        await bot_app.start()
        logger.info("Telegram bot initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Telegram bot: {e}")
        logger.warning("Application will continue without bot functionality")
        bot_app = None

    logger.info("Application started successfully")

    yield

    # Shutdown
    logger.info("Shutting down application...")

    if bot_app:
        try:
            await bot_app.stop()
            await bot_app.shutdown()
        except Exception as e:
            logger.error(f"Error shutting down bot: {e}")

    await db.disconnect()

    logger.info("Application shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="Vouch Portal",
    description="Community trust and reputation system for Telegram",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Security middleware to sanitize all JSON responses
@app.middleware("http")
async def sanitize_responses(request: Request, call_next):
    """Middleware to automatically sanitize all JSON responses"""
    response = await call_next(request)
    
    # Check if this is a JSON response (use startswith to catch charset variations)
    content_type = response.headers.get("content-type", "")
    if content_type.startswith("application/json"):
        try:
            import json
            from fastapi.responses import JSONResponse
            
            # Read response body
            body = b""
            async for chunk in response.body_iterator:
                body += chunk
            
            # Parse and sanitize
            data = json.loads(body)
            sanitized_data = sanitize_response_data(data)
            
            # Preserve important headers but exclude Content-Length (FastAPI will recalculate)
            preserved_headers = {}
            for key, value in response.headers.items():
                if key.lower() not in ['content-length', 'content-type']:
                    preserved_headers[key] = value
            
            # Return sanitized response with preserved headers
            return JSONResponse(
                content=sanitized_data,
                status_code=response.status_code,
                headers=preserved_headers
            )
        except Exception as e:
            logger.error(f"Error in sanitize middleware: {e}")
            # Return original response on error
            from fastapi.responses import Response
            return Response(
                content=body if 'body' in locals() else b"",
                status_code=response.status_code,
                headers=dict(response.headers)
            )
    
    return response

# Mount static files
try:
    app.mount("/static", StaticFiles(directory="webapp/static"), name="static")
except Exception as e:
    logger.warning(f"Could not mount static files: {e}")


# Pydantic models
class VouchRequest(BaseModel):
    from_user_id: int
    to_username: str
    message: Optional[str] = None
    vote_type: str = 'positive'  # 'positive' or 'negative'


class InviteRequest(BaseModel):
    from_user_id: int
    to_username: str


class ProfileUpdateRequest(BaseModel):
    user_id: int
    bio: Optional[str] = None
    location: Optional[str] = None
    profile_picture_url: Optional[str] = None


# Routes
@app.get("/", response_class=HTMLResponse)
async def serve_webapp():
    """Serve the main WebApp"""
    try:
        with open("webapp/index.html", "r", encoding="utf-8") as f:
            html_content = f.read()
        return HTMLResponse(content=html_content)
    except FileNotFoundError:
        return HTMLResponse(
            content="<h1>Vouch Portal</h1><p>WebApp frontend not found. Please ensure webapp/index.html exists.</p>",
            status_code=200
        )


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "vouch-portal",
        "database": "connected" if db.pool else "disconnected"
    }


@app.get("/api/bot-info")
async def get_bot_info():
    """Get bot configuration info"""
    return {
        "bot_username": os.getenv("BOT_USERNAME", "VouchPortalBot")
    }


@app.post("/webhook")
async def webhook(request: Request):
    """Handle Telegram webhook updates"""
    if not bot_app:
        return {"status": "error", "message": "Bot not initialized"}
    
    try:
        data = await request.json()
        update = Update.de_json(data, bot_app.bot)

        # Process update
        await bot_app.process_update(update)

        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return {"status": "error", "message": str(e)}


@app.get("/api/users")
async def get_users(limit: int = 100, offset: int = 0):
    """Get list of all users"""
    try:
        users = await db.get_all_users(limit=limit, offset=offset)

        # Enhance with rank info and sanitize profile URLs
        for user in users:
            user["rank_emoji"] = db.get_rank_emoji(user["rank"])
            user["rank_name"] = db.get_rank_name(user["rank"])
            sanitize_user_profile_url(user)

        return {"users": users}
    except Exception as e:
        logger.error(f"Error getting users: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/profile/{user_id}")
async def get_profile(user_id: int):
    """Get user profile with vouches"""
    try:
        # Get user data
        user = await db.get_user(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Sanitize profile URL to prevent token leaks
        sanitize_user_profile_url(user)

        # Get vouches
        vouches_received = await db.get_vouches_for_user(user_id)
        vouches_given = await db.get_vouches_by_user(user_id)

        # Add rank info
        user["rank_emoji"] = db.get_rank_emoji(user["rank"])
        user["rank_name"] = db.get_rank_name(user["rank"])

        # Calculate next rank info
        next_rank_threshold = 0
        if user["total_vouches"] < 3:
            next_rank_threshold = 3
        elif user["total_vouches"] < 6:
            next_rank_threshold = 6
        elif user["total_vouches"] < 11:
            next_rank_threshold = 11
        elif user["total_vouches"] < 16:
            next_rank_threshold = 16
        else:
            next_rank_threshold = user["total_vouches"]

        progress_percentage = 0
        if next_rank_threshold > 0 and user["total_vouches"] < 16:
            current_tier_start = 0
            if user["total_vouches"] >= 11:
                current_tier_start = 11
            elif user["total_vouches"] >= 6:
                current_tier_start = 6
            elif user["total_vouches"] >= 3:
                current_tier_start = 3

            progress_percentage = ((user["total_vouches"] - current_tier_start) /
                                   (next_rank_threshold - current_tier_start)) * 100

        return {
            "user": user,
            "vouches_received": vouches_received,
            "vouches_given": vouches_given,
            "next_rank_threshold": next_rank_threshold,
            "progress_percentage": min(100, max(0, progress_percentage))
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/vouch")
async def create_vouch(vouch_request: VouchRequest):
    """Create a new vouch - works for both existing users and pending vouches"""
    try:
        # Sanitize message
        message = ""
        if vouch_request.message:
            message = sanitize_message(vouch_request.message)

        # Create vouch (works for both existing and non-existing users)
        target_username = vouch_request.to_username.replace("@", "")
        result = await db.create_vouch(
            from_user_id=vouch_request.from_user_id,
            to_username=target_username,
            message=message if message else "",
            vote_type=vouch_request.vote_type
        )

        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])

        # Check if this was a pending vouch or immediate vouch
        if result.get("is_pending"):
            # Pending vouch for user who hasn't joined yet
            return {
                "success": True,
                "vouch": result,
                "pending": True,
                "message": f"Vouch recorded for @{target_username}. They'll receive it when they join!"
            }
        else:
            # Immediate vouch for existing user
            to_user_id = result.get("to_user_id")
            
            if not to_user_id:
                raise HTTPException(status_code=400, detail="Invalid user ID")
            
            # Get updated profile
            profile = await get_profile(int(to_user_id))

            return {
                "success": True,
                "vouch": result,
                "pending": False,
                "profile": profile
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating vouch: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/vouches/{vouch_id}")
async def update_vouch(vouch_id: int, vouch_update: dict):
    """Update an existing vouch message - only the creator can edit"""
    if not db.pool:
        raise HTTPException(status_code=503, detail="Database not available")
    
    try:
        from_user_id = vouch_update.get("from_user_id")
        new_message = vouch_update.get("message", "")
        
        if not from_user_id:
            raise HTTPException(status_code=400, detail="from_user_id is required")
        
        # Sanitize the new message
        sanitized_message = sanitize_message(new_message) if new_message else ""
        
        # Update the vouch
        result = await db.update_vouch(vouch_id, from_user_id, sanitized_message)
        
        if "error" in result:
            # Return 404 if vouch not found, 403 if permission denied
            if result["error"] == "Vouch not found":
                raise HTTPException(status_code=404, detail=result["error"])
            else:
                raise HTTPException(status_code=403, detail=result["error"])
        
        return {
            "success": True,
            "vouch": result
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating vouch: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/profile/update")
async def update_profile(profile_update: ProfileUpdateRequest):
    """Update user profile information"""
    if not db.pool:
        raise HTTPException(status_code=503, detail="Database not available")
    
    try:
        async with db.pool.acquire() as conn:
            # Build update query dynamically
            updates = []
            params = []
            param_count = 1
            
            if profile_update.bio is not None:
                updates.append(f"bio = ${param_count}")
                params.append(profile_update.bio[:500])  # Limit bio to 500 chars
                param_count += 1
            
            if profile_update.location is not None:
                updates.append(f"location = ${param_count}")
                params.append(profile_update.location[:100])  # Limit location to 100 chars
                param_count += 1
            
            if profile_update.profile_picture_url is not None:
                # Validate: only allow file_ids, reject URLs containing api.telegram.org
                if "api.telegram.org" in profile_update.profile_picture_url:
                    raise HTTPException(status_code=400, detail="Invalid profile picture URL. Use file_id only.")
                updates.append(f"profile_picture_url = ${param_count}")
                params.append(profile_update.profile_picture_url)
                param_count += 1
            
            if not updates:
                raise HTTPException(status_code=400, detail="No fields to update")
            
            params.append(profile_update.user_id)
            query = f"UPDATE users SET {', '.join(updates)} WHERE telegram_user_id = ${param_count} RETURNING *"
            
            updated_user = await conn.fetchrow(query, *params)
            
            if not updated_user:
                raise HTTPException(status_code=404, detail="User not found")
            
            user_dict = dict(updated_user)
            # Sanitize response to prevent any token leaks
            sanitize_user_profile_url(user_dict)
            
            return {
                "success": True,
                "user": user_dict
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/profile-photo/{user_id}")
async def fetch_profile_photo_file_id(user_id: int):
    """Fetch and cache user's Telegram profile photo file_id"""
    try:
        from bot import get_user_profile_photo_file_id
        
        # Check if we already have a cached file_id
        user = await db.get_user(user_id)
        if user and user.get("profile_picture_url"):
            # profile_picture_url now stores file_id
            return {
                "success": True,
                "file_id": user["profile_picture_url"],
                "cached": True
            }
        
        # Fetch from Telegram
        file_id = await get_user_profile_photo_file_id(user_id)
        
        if file_id:
            # Cache file_id in database (using profile_picture_url column)
            pool = db._ensure_connected()
            async with pool.acquire() as conn:
                await conn.execute(
                    "UPDATE users SET profile_picture_url = $1 WHERE telegram_user_id = $2",
                    file_id,
                    user_id
                )
            
            return {
                "success": True,
                "file_id": file_id,
                "cached": False
            }
        else:
            return {
                "success": False,
                "message": "No profile photo available"
            }
            
    except Exception as e:
        logger.error(f"Error fetching profile photo: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/photo-proxy/{file_id}")
async def proxy_profile_photo(file_id: str):
    """Proxy endpoint to serve Telegram profile photos without exposing bot token"""
    try:
        from bot import download_profile_photo_bytes
        from fastapi.responses import Response
        
        # Download photo bytes from Telegram
        photo_bytes = await download_profile_photo_bytes(file_id)
        
        if photo_bytes:
            # Return image with appropriate headers
            return Response(
                content=photo_bytes,
                media_type="image/jpeg",
                headers={
                    "Cache-Control": "public, max-age=86400"  # Cache for 24 hours
                }
            )
        else:
            raise HTTPException(status_code=404, detail="Photo not found")
            
    except Exception as e:
        logger.error(f"Error proxying profile photo: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/invite")
async def send_invite(invite_request: InviteRequest):
    """Send vouch invite to another user"""
    if not db.pool or not bot_app:
        raise HTTPException(status_code=503, detail="Service not available")
    
    try:
        # Check rate limit
        can_send = await db.can_send_invite(
            invite_request.from_user_id,
            invite_request.to_username.replace("@", "")
        )

        if not can_send:
            raise HTTPException(
                status_code=429,
                detail="You can only invite this user once per week"
            )

        # Log invite
        await db.log_invite(
            invite_request.from_user_id,
            invite_request.to_username.replace("@", "")
        )

        # Get inviter info
        inviter = await db.get_user(invite_request.from_user_id)

        # Send DM via bot (if user exists)
        try:
            async with db.pool.acquire() as conn:
                target_user = await conn.fetchrow(
                    "SELECT telegram_user_id FROM users WHERE username = $1",
                    invite_request.to_username.replace("@", "")
                )

            if target_user:
                # NOTIFICATIONS DISABLED - No invite messages sent
                # Just log the event without sending DM
                await db.log_event("invite_logged", invite_request.from_user_id, {
                    "to_username": invite_request.to_username
                })

                return {"success": True, "message": "Invite recorded"}
        except Exception as e:
            logger.error(f"Failed to send invite DM: {e}")
            # Log cooldown anyway
            await db.log_event("invite_cooldown_blocked", invite_request.from_user_id, {
                "to_username": invite_request.to_username
            })
            return {"success": True, "message": "Invite recorded (user not found on Telegram)"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending invite: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/analytics")
async def get_analytics(user_id: Optional[int] = None):
    """Get analytics data (admin only or user-specific)"""
    try:
        # Get analytics summary
        analytics = await db.get_analytics_summary()

        return analytics
    except Exception as e:
        logger.error(f"Error getting analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/activity")
async def get_activity(limit: int = 50):
    """Get recent community activity feed"""
    try:
        activity = await db.get_recent_activity(limit)
        return {"activity": activity}
    except Exception as e:
        logger.error(f"Error getting activity: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/leaderboards/{board_type}")
async def get_leaderboard_by_type(board_type: str, limit: int = 20):
    """Get leaderboard data - supports: most_vouched, top_givers, rising_stars, streak_leaders"""
    try:
        leaderboard = await db.get_leaderboard(board_type, limit)
        
        # Add rank info and sanitize profile URLs
        for user in leaderboard:
            user["rank_emoji"] = db.get_rank_emoji(user["rank"])
            user["rank_name"] = db.get_rank_name(user["rank"])
            sanitize_user_profile_url(user)
        
        return {"leaderboard": leaderboard, "board_type": board_type}
    except Exception as e:
        logger.error(f"Error getting leaderboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/referrals/{user_id}")
async def get_referral_stats(user_id: int):
    """Get referral statistics for a user"""
    try:
        stats = await db.get_user_referral_stats(user_id)
        
        # Add rank info and sanitize profile URLs
        for referral in stats["recent_referrals"]:
            referral["rank_emoji"] = db.get_rank_emoji(referral["rank"])
            referral["rank_name"] = db.get_rank_name(referral["rank"])
            sanitize_user_profile_url(referral)
        
        return stats
    except Exception as e:
        logger.error(f"Error getting referral stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/viral/summary")
async def get_viral_summary():
    """Get viral growth summary"""
    if not db.pool:
        raise HTTPException(status_code=503, detail="Database not available")
    
    try:
        async with db.pool.acquire() as conn:
            # Vouches today
            vouches_today = await conn.fetchval("""
                SELECT COUNT(*) FROM vouches
                WHERE created_at > NOW() - INTERVAL '24 hours'
            """)

            # Referral stats
            referral_signups = await conn.fetchval("""
                SELECT COUNT(*) FROM users WHERE referrer_id IS NOT NULL
            """)

            # Recent activity
            recent_vouches = await conn.fetch("""
                SELECT v.*, u1.username as from_username, u2.username as to_username
                FROM vouches v
                JOIN users u1 ON v.from_user_id = u1.telegram_user_id
                JOIN users u2 ON v.to_user_id = u2.telegram_user_id
                ORDER BY v.created_at DESC
                LIMIT 10
            """)

        return {
            "vouches_today": vouches_today,
            "referral_signups": referral_signups,
            "recent_activity": [dict(v) for v in recent_vouches]
        }
    except Exception as e:
        logger.error(f"Error getting viral summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/search")
async def search_users(q: str, limit: int = 20):
    """Search users by username or name"""
    if not db.pool:
        raise HTTPException(status_code=503, detail="Database not available")
    
    try:
        async with db.pool.acquire() as conn:
            users = await conn.fetch("""
                SELECT telegram_user_id, username, first_name, last_name, rank, total_vouches
                FROM users
                WHERE username ILIKE $1 OR first_name ILIKE $1 OR last_name ILIKE $1
                ORDER BY total_vouches DESC
                LIMIT $2
            """, f"%{q}%", limit)

        result_users = [dict(u) for u in users]

        # Add rank info and sanitize profile URLs
        for user in result_users:
            user["rank_emoji"] = db.get_rank_emoji(user["rank"])
            user["rank_name"] = db.get_rank_name(user["rank"])
            sanitize_user_profile_url(user)

        return {"users": result_users}
    except Exception as e:
        logger.error(f"Error searching users: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/leaderboard")
async def get_leaderboard(period: str = "all"):
    """Get leaderboard data"""
    try:
        analytics = await db.get_analytics_summary()

        # Sanitize profile URLs in leaderboard data
        for user in analytics.get("most_vouched", []):
            sanitize_user_profile_url(user)
        for user in analytics.get("top_helpers", []):
            sanitize_user_profile_url(user)

        return {
            "most_vouched": analytics["most_vouched"],
            "top_helpers": analytics["top_helpers"]
        }
    except Exception as e:
        logger.error(f"Error getting leaderboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/share")
async def log_share(user_id: int, platform: str):
    """Log share event"""
    try:
        await db.log_event("share_clicked", user_id, {"platform": platform})
        return {"success": True}
    except Exception as e:
        logger.error(f"Error logging share: {e}")
        return {"success": False}


# Admin endpoints
@app.get("/api/admin/config")
async def get_admin_config(admin_id: int):
    """Get admin configuration (admin only)"""
    if admin_id != ADMIN_ID:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    if not db.pool:
        raise HTTPException(status_code=503, detail="Database not available")

    try:
        async with db.pool.acquire() as conn:
            config = await conn.fetch("SELECT * FROM bot_config")

        return {"config": [dict(c) for c in config]}
    except Exception as e:
        logger.error(f"Error getting admin config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/admin/config")
async def update_admin_config(admin_id: int, key: str, value: str):
    """Update admin configuration (admin only)"""
    if admin_id != ADMIN_ID:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    if not db.pool:
        raise HTTPException(status_code=503, detail="Database not available")

    try:
        async with db.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO bot_config (key, value)
                VALUES ($1, $2)
                ON CONFLICT (key) DO UPDATE SET value = $2, updated_at = NOW()
            """, key, value)

        return {"success": True}
    except Exception as e:
        logger.error(f"Error updating admin config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "5000"))
    
    is_production = os.getenv("REPLIT_ENVIRONMENT", "development") == "production"
    
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=port, 
        reload=not is_production
    )
