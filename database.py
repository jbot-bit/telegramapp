"""
Database module for Vouch Portal
Handles PostgreSQL connections and schema management
"""
import asyncpg
import os
from datetime import datetime
from typing import Optional, List, Dict, Any
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None
        self.database_url = os.getenv("DATABASE_URL")

    async def connect(self):
        """Initialize database connection pool"""
        try:
            self.pool = await asyncpg.create_pool(
                self.database_url,
                min_size=2,
                max_size=10,
                command_timeout=60
            )
            logger.info("Database pool created successfully")
            await self.init_schema()
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise

    async def disconnect(self):
        """Close database connection pool"""
        if self.pool:
            await self.pool.close()
            logger.info("Database pool closed")

    async def init_schema(self):
        """Create all necessary tables if they don't exist"""
        async with self.pool.acquire() as conn:
            # Users table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    telegram_user_id BIGINT PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    bio TEXT,
                    profile_picture_url TEXT,
                    location TEXT,
                    first_seen_at TIMESTAMP DEFAULT NOW(),
                    total_vouches INTEGER DEFAULT 0,
                    rank TEXT DEFAULT 'unverified',
                    last_active_at TIMESTAMP DEFAULT NOW(),
                    referrer_id BIGINT,
                    streak_days INTEGER DEFAULT 0,
                    last_streak_date DATE
                )
            """)
            
            # Add new profile columns if they don't exist (for existing databases)
            try:
                await conn.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS bio TEXT")
                await conn.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS profile_picture_url TEXT")
                await conn.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS location TEXT")
            except Exception as e:
                logger.warning(f"Profile columns update warning (might be expected): {e}")

            # Vouches table - supports pending vouches for users who haven't joined yet
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS vouches (
                    id SERIAL PRIMARY KEY,
                    from_user_id BIGINT REFERENCES users(telegram_user_id),
                    to_user_id BIGINT REFERENCES users(telegram_user_id),
                    to_username TEXT,
                    message TEXT,
                    created_at TIMESTAMP DEFAULT NOW(),
                    approved BOOLEAN DEFAULT TRUE,
                    is_pending BOOLEAN DEFAULT FALSE
                )
            """)
            
            # Add columns if they don't exist (for existing databases)
            try:
                await conn.execute("ALTER TABLE vouches ADD COLUMN IF NOT EXISTS to_username TEXT")
                await conn.execute("ALTER TABLE vouches ADD COLUMN IF NOT EXISTS is_pending BOOLEAN DEFAULT FALSE")
                await conn.execute("ALTER TABLE vouches ALTER COLUMN to_user_id DROP NOT NULL")
            except Exception as e:
                logger.warning(f"Schema update warning (might be expected): {e}")

            # Bot config table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS bot_config (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    updated_at TIMESTAMP DEFAULT NOW()
                )
            """)

            # Events/Analytics table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    id SERIAL PRIMARY KEY,
                    event_type TEXT NOT NULL,
                    user_id BIGINT,
                    metadata JSONB,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)

            # Rank events table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS rank_events (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT REFERENCES users(telegram_user_id),
                    old_rank TEXT,
                    new_rank TEXT,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)

            # Invite tracking
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS invites (
                    id SERIAL PRIMARY KEY,
                    from_user_id BIGINT REFERENCES users(telegram_user_id),
                    to_username TEXT,
                    sent_at TIMESTAMP DEFAULT NOW()
                )
            """)

            # Create indexes
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_vouches_to_user ON vouches(to_user_id)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_vouches_from_user ON vouches(from_user_id)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_events_created ON events(created_at)")

            logger.info("Database schema initialized successfully")

    # User operations
    async def get_or_create_user(self, telegram_user_id: int, username: str = None,
                                  first_name: str = None, last_name: str = None,
                                  referrer_id: int = None) -> Dict[str, Any]:
        """Get user or create if doesn't exist"""
        async with self.pool.acquire() as conn:
            user = await conn.fetchrow(
                "SELECT * FROM users WHERE telegram_user_id = $1",
                telegram_user_id
            )

            if user:
                # Update last active and username if provided
                if username:
                    old_username = user["username"]
                    await conn.execute(
                        "UPDATE users SET last_active_at = NOW(), username = $2 WHERE telegram_user_id = $1",
                        telegram_user_id, username
                    )
                    # Process pending vouches if username changed or was newly set
                    if old_username != username:
                        await self._process_pending_vouches(telegram_user_id, username)
                else:
                    await conn.execute(
                        "UPDATE users SET last_active_at = NOW() WHERE telegram_user_id = $1",
                        telegram_user_id
                    )
                return dict(user)
            else:
                # Create new user
                user = await conn.fetchrow("""
                    INSERT INTO users (telegram_user_id, username, first_name, last_name, referrer_id)
                    VALUES ($1, $2, $3, $4, $5)
                    RETURNING *
                """, telegram_user_id, username, first_name, last_name, referrer_id)

                # Log signup event
                await self.log_event("user_signup", telegram_user_id, {
                    "referrer_id": referrer_id,
                    "username": username
                })

                # Process pending vouches for this user (if they have a username)
                if username:
                    await self._process_pending_vouches(telegram_user_id, username)

                return dict(user)

    async def get_user(self, telegram_user_id: int) -> Optional[Dict[str, Any]]:
        """Get user by telegram ID"""
        async with self.pool.acquire() as conn:
            user = await conn.fetchrow(
                "SELECT * FROM users WHERE telegram_user_id = $1",
                telegram_user_id
            )
            return dict(user) if user else None

    async def _process_pending_vouches(self, telegram_user_id: int, username: str):
        """Convert pending vouches to actual vouches when a user signs up or changes username"""
        async with self.pool.acquire() as conn:
            # Normalize username for case-insensitive matching
            username_normalized = username.lower() if username else None
            if not username_normalized:
                return
            
            # Find all pending vouches for this username (case-insensitive)
            pending_vouches = await conn.fetch(
                "SELECT * FROM vouches WHERE LOWER(to_username) = $1 AND is_pending = TRUE",
                username_normalized
            )
            
            if not pending_vouches:
                return
            
            logger.info(f"Processing {len(pending_vouches)} pending vouches for @{username}")
            
            # Convert each pending vouch to a real vouch
            for vouch in pending_vouches:
                # Update the vouch to link to the actual user
                await conn.execute("""
                    UPDATE vouches 
                    SET to_user_id = $1, is_pending = FALSE 
                    WHERE id = $2
                """, telegram_user_id, vouch["id"])
            
            # Update the user's total vouch count
            vouch_count = len(pending_vouches)
            await conn.execute(
                "UPDATE users SET total_vouches = total_vouches + $1 WHERE telegram_user_id = $2",
                vouch_count, telegram_user_id
            )
            
            # Get updated vouch count and recalculate rank
            total_vouches = await conn.fetchval(
                "SELECT total_vouches FROM users WHERE telegram_user_id = $1",
                telegram_user_id
            )
            
            new_rank = self.calculate_rank(total_vouches)
            await conn.execute(
                "UPDATE users SET rank = $1 WHERE telegram_user_id = $2",
                new_rank, telegram_user_id
            )
            
            # Log event
            await self.log_event("pending_vouches_processed", telegram_user_id, {
                "username": username,
                "vouches_processed": vouch_count,
                "new_rank": new_rank
            })

    async def get_all_users(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Get all users with pagination"""
        async with self.pool.acquire() as conn:
            users = await conn.fetch(
                "SELECT * FROM users ORDER BY total_vouches DESC LIMIT $1 OFFSET $2",
                limit, offset
            )
            return [dict(user) for user in users]

    async def update_user_rank(self, telegram_user_id: int, new_rank: str) -> None:
        """Update user rank and log event"""
        async with self.pool.acquire() as conn:
            old_rank = await conn.fetchval(
                "SELECT rank FROM users WHERE telegram_user_id = $1",
                telegram_user_id
            )

            await conn.execute(
                "UPDATE users SET rank = $1 WHERE telegram_user_id = $2",
                new_rank, telegram_user_id
            )

            # Log rank change event
            await conn.execute("""
                INSERT INTO rank_events (user_id, old_rank, new_rank)
                VALUES ($1, $2, $3)
            """, telegram_user_id, old_rank, new_rank)

            await self.log_event("rank_up", telegram_user_id, {
                "old_rank": old_rank,
                "new_rank": new_rank
            })

    # Vouch operations
    async def create_vouch(self, from_user_id: int, to_user_id: int = None, to_username: str = None, message: str = None) -> Dict[str, Any]:
        """Create a new vouch - supports both existing users and pending vouches for users who haven't joined yet"""
        async with self.pool.acquire() as conn:
            # Normalize username (case-insensitive, remove @)
            if to_username:
                to_username = to_username.replace("@", "").lower()
            
            # If username is provided, try to find the user (case-insensitive)
            if to_username and not to_user_id:
                user = await conn.fetchrow(
                    "SELECT telegram_user_id FROM users WHERE LOWER(username) = $1",
                    to_username
                )
                if user:
                    to_user_id = user["telegram_user_id"]
            
            # Check if vouch already exists (either by ID or username)
            if to_user_id:
                existing = await conn.fetchrow(
                    "SELECT * FROM vouches WHERE from_user_id = $1 AND to_user_id = $2",
                    from_user_id, to_user_id
                )
            elif to_username:
                existing = await conn.fetchrow(
                    "SELECT * FROM vouches WHERE from_user_id = $1 AND LOWER(to_username) = $2 AND is_pending = TRUE",
                    from_user_id, to_username
                )
            else:
                return {"error": "Must provide either to_user_id or to_username"}

            if existing:
                return {"error": "You already vouched for this user"}

            # Check for self-vouch (only if we have to_user_id)
            if to_user_id and to_user_id == from_user_id:
                return {"error": "You cannot vouch for yourself"}

            # Create vouch (either confirmed or pending)
            if to_user_id:
                # User exists - create confirmed vouch
                vouch = await conn.fetchrow("""
                    INSERT INTO vouches (from_user_id, to_user_id, to_username, message, is_pending)
                    VALUES ($1, $2, $3, $4, FALSE)
                    RETURNING *
                """, from_user_id, to_user_id, to_username if to_username else None, message)

                # Update total vouches count
                await conn.execute(
                    "UPDATE users SET total_vouches = total_vouches + 1 WHERE telegram_user_id = $1",
                    to_user_id
                )

                # Get updated vouch count
                vouch_count = await conn.fetchval(
                    "SELECT total_vouches FROM users WHERE telegram_user_id = $1",
                    to_user_id
                )

                # Calculate and update rank
                new_rank = self.calculate_rank(vouch_count)
                current_rank = await conn.fetchval(
                    "SELECT rank FROM users WHERE telegram_user_id = $1",
                    to_user_id
                )

                if new_rank != current_rank:
                    await self.update_user_rank(to_user_id, new_rank)

                # Check for mutual vouch
                mutual = await conn.fetchrow(
                    "SELECT * FROM vouches WHERE from_user_id = $1 AND to_user_id = $2",
                    to_user_id, from_user_id
                )

                if mutual:
                    await self.log_event("mutual_vouch", from_user_id, {
                        "other_user": to_user_id
                    })

                await self.log_event("vouch_created", from_user_id, {
                    "to_user": to_user_id,
                    "vouch_count": vouch_count
                })
            else:
                # User doesn't exist - create pending vouch
                vouch = await conn.fetchrow("""
                    INSERT INTO vouches (from_user_id, to_user_id, to_username, message, is_pending)
                    VALUES ($1, NULL, $2, $3, TRUE)
                    RETURNING *
                """, from_user_id, to_username, message)

                await self.log_event("pending_vouch_created", from_user_id, {
                    "to_username": to_username,
                })

            return dict(vouch)

    async def get_vouches_for_user(self, telegram_user_id: int) -> List[Dict[str, Any]]:
        """Get all vouches received by a user"""
        async with self.pool.acquire() as conn:
            vouches = await conn.fetch("""
                SELECT v.*, u.username, u.first_name, u.rank
                FROM vouches v
                JOIN users u ON v.from_user_id = u.telegram_user_id
                WHERE v.to_user_id = $1
                ORDER BY v.created_at DESC
            """, telegram_user_id)
            return [dict(vouch) for vouch in vouches]

    async def get_vouches_by_user(self, telegram_user_id: int) -> List[Dict[str, Any]]:
        """Get all vouches given by a user"""
        async with self.pool.acquire() as conn:
            vouches = await conn.fetch("""
                SELECT v.*, u.username, u.first_name, u.rank
                FROM vouches v
                JOIN users u ON v.to_user_id = u.telegram_user_id
                WHERE v.from_user_id = $1
                ORDER BY v.created_at DESC
            """, telegram_user_id)
            return [dict(vouch) for vouch in vouches]

    # Analytics operations
    async def log_event(self, event_type: str, user_id: int = None, metadata: Dict = None):
        """Log an analytics event"""
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO events (event_type, user_id, metadata)
                VALUES ($1, $2, $3)
            """, event_type, user_id, metadata)

    async def get_analytics_summary(self) -> Dict[str, Any]:
        """Get analytics summary for dashboard"""
        async with self.pool.acquire() as conn:
            # Total users
            total_users = await conn.fetchval("SELECT COUNT(*) FROM users")

            # Active users (last 24h, 7d, 30d)
            active_24h = await conn.fetchval(
                "SELECT COUNT(*) FROM users WHERE last_active_at > NOW() - INTERVAL '24 hours'"
            )
            active_7d = await conn.fetchval(
                "SELECT COUNT(*) FROM users WHERE last_active_at > NOW() - INTERVAL '7 days'"
            )
            active_30d = await conn.fetchval(
                "SELECT COUNT(*) FROM users WHERE last_active_at > NOW() - INTERVAL '30 days'"
            )

            # New signups (last 7 days)
            new_signups = await conn.fetchval(
                "SELECT COUNT(*) FROM users WHERE first_seen_at > NOW() - INTERVAL '7 days'"
            )

            # Total vouches
            total_vouches = await conn.fetchval("SELECT COUNT(*) FROM vouches")

            # Rank distribution
            rank_dist = await conn.fetch(
                "SELECT rank, COUNT(*) as count FROM users GROUP BY rank"
            )

            # Top helpers (users who gave most vouches)
            top_helpers = await conn.fetch("""
                SELECT u.telegram_user_id, u.username, u.first_name, COUNT(v.id) as vouch_count
                FROM users u
                JOIN vouches v ON u.telegram_user_id = v.from_user_id
                WHERE v.created_at > NOW() - INTERVAL '7 days'
                GROUP BY u.telegram_user_id, u.username, u.first_name
                ORDER BY vouch_count DESC
                LIMIT 10
            """)

            # Most vouched users
            most_vouched = await conn.fetch("""
                SELECT telegram_user_id, username, first_name, total_vouches, rank
                FROM users
                ORDER BY total_vouches DESC
                LIMIT 10
            """)

            # Mutual vouch rate
            mutual_vouch_count = await conn.fetchval("""
                SELECT COUNT(*) FROM events WHERE event_type = 'mutual_vouch'
            """)

            return {
                "total_users": total_users,
                "active_users": {
                    "24h": active_24h,
                    "7d": active_7d,
                    "30d": active_30d
                },
                "new_signups_7d": new_signups,
                "total_vouches": total_vouches,
                "rank_distribution": [{"rank": r["rank"], "count": r["count"]} for r in rank_dist],
                "top_helpers": [dict(h) for h in top_helpers],
                "most_vouched": [dict(m) for m in most_vouched],
                "mutual_vouch_count": mutual_vouch_count
            }

    async def can_send_invite(self, from_user_id: int, to_username: str) -> bool:
        """Check if invite can be sent (rate limiting)"""
        async with self.pool.acquire() as conn:
            recent_invite = await conn.fetchrow("""
                SELECT * FROM invites
                WHERE from_user_id = $1 AND to_username = $2
                AND sent_at > NOW() - INTERVAL '7 days'
            """, from_user_id, to_username)

            return recent_invite is None

    async def log_invite(self, from_user_id: int, to_username: str):
        """Log an invite sent"""
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO invites (from_user_id, to_username)
                VALUES ($1, $2)
            """, from_user_id, to_username)

    @staticmethod
    def calculate_rank(vouch_count: int) -> str:
        """Calculate rank based on vouch count"""
        if vouch_count >= 16:
            return "top_tier"
        elif vouch_count >= 11:
            return "endorsed"
        elif vouch_count >= 6:
            return "trusted"
        elif vouch_count >= 3:
            return "verified"
        else:
            return "unverified"

    @staticmethod
    def get_rank_emoji(rank: str) -> str:
        """Get emoji for rank"""
        rank_emojis = {
            "unverified": "🚫",
            "verified": "✅",
            "trusted": "🔷",
            "endorsed": "🛡",
            "top_tier": "👑"
        }
        return rank_emojis.get(rank, "❓")

    @staticmethod
    def get_rank_name(rank: str) -> str:
        """Get display name for rank"""
        rank_names = {
            "unverified": "Unverified",
            "verified": "Verified",
            "trusted": "Trusted",
            "endorsed": "Endorsed",
            "top_tier": "Top-Tier Verified"
        }
        return rank_names.get(rank, "Unknown")

# Global database instance
db = Database()
