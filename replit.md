# Vouch Portal - Telegram Mini WebApp

## Overview

Vouch Portal is a community trust and reputation system built as a Telegram Mini WebApp. It enables users to vouch for each other, building reputation through peer verification. Users progress through 5 reputation ranks (Unverified → Verified → Trusted → Endorsed → Top-Tier Verified) based on vouches received from community members.

The application combines a FastAPI backend, PostgreSQL database, Telegram Bot integration, and a mobile-first web interface to create a viral growth engine focused on reciprocity, social proof, and status progression.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Backend Architecture

**Framework**: FastAPI (Python 3.12)
- Chosen for its async support, automatic API documentation, and performance
- Uses uvicorn as the ASGI server
- Implements lifespan management for database and bot initialization
- Handles both REST API endpoints and Telegram webhook processing

**API Design**:
- RESTful endpoints for user profiles, vouches, analytics, and community data
- WebApp served via static file mounting
- CORS middleware configured for cross-origin requests
- Error handling with graceful degradation (app continues even if bot initialization fails)

**Telegram Bot Integration**:
- python-telegram-bot library for bot handlers
- Webhook-based architecture (not polling) for production efficiency
- Command handlers: /start, /profile, /vouch, /leaderboard, /stats
- Callback query handlers for inline keyboard interactions
- Content moderation with banned word filtering and message sanitization

**Rate Limiting & Moderation**:
- Invite cooldowns (7 days per voucher handle)
- Message length limits (120 characters)
- Banned word filtering with [redacted] replacements
- Prevents spam and maintains community safety

### Frontend Architecture

**Technology Stack**: Vanilla JavaScript + HTML5 + CSS3
- No framework dependencies for faster load times on mobile
- Telegram WebApp SDK integration for native-like experience
- Canvas Confetti library for celebration animations

**UI Design**:
- Mobile-first, dark theme matching Telegram's aesthetic
- Tab-based navigation (Profile, Vouch, Community, Insights)
- Progressive enhancement approach
- Responsive grid layouts and flexbox
- Sticky header with persistent navigation

**State Management**:
- Client-side state using JavaScript closures
- No external state management library
- Real-time updates via API polling where needed
- LocalStorage for minimal caching (if implemented)

**User Experience**:
- One-tap actions with instant visual feedback
- Micro-animations and confetti celebrations on milestones
- Toast notifications for user actions
- Loading states and error handling
- Username sanitization and validation

### Data Architecture

**Database**: PostgreSQL with asyncpg driver
- Connection pooling (min: 2, max: 10 connections)
- Async operations for non-blocking I/O
- Schema initialization on startup

**Core Tables**:

1. **users**: Telegram user profiles, ranks, vouch counts, streaks, bio, location
2. **vouches**: From/to relationships, messages, timestamps, approval status
3. **events**: Rank changes, referrals, mutual vouches, system events
4. **invite_tracking**: Cooldown management for invite spam prevention
5. **config**: System-wide configuration storage (JSON)

**Rank Calculation Logic**:
- Unverified: 0-2 vouches
- Verified: 3-5 vouches
- Trusted: 6-10 vouches
- Endorsed: 11-15 vouches
- Top-Tier Verified: 16+ vouches

**Analytics Tracking**:
- User activity metrics (DAU, MAU, signups)
- Vouch interaction patterns
- Mutual-vouch conversion rates
- Referral attribution via deep links
- Leaderboard calculations (weekly top helpers)

### Viral Growth Mechanics

**Design Philosophy**: Organic growth through reciprocity, status, and social proof without spam.

**Core Loops**:
1. **Mutual-Vouch Loop**: Post-vouch prompts to reciprocate within 48 hours
2. **Rank-Share Loop**: Share achievements via Telegram on rank-up
3. **Invite-to-Verify Loop**: Polite DM to nominated users (7-day cooldown)
4. **Top Helpers Loop**: Weekly leaderboard recognition

**Deep Linking**:
- Start parameters track referral sources: `t.me/{BOT_USERNAME}?startapp=profile_{TG_ID}`
- Enables attribution of viral spread
- Powers referral dashboard in analytics

**Content Safety**:
- All copy uses positive, neutral, communal language
- Avoids negative words (scam, fraud, report)
- Uses trust-focused vocabulary (verify, build reputation, community)

### Deployment Architecture

**Hosting**: Replit (or any cloud platform supporting Python/FastAPI)
- Environment variables via Replit Secrets
- Automatic HTTPS via Replit domains
- Zero-downtime deploys with uvicorn auto-reload

**Configuration Management**:
- BOT_TOKEN: Telegram bot authentication
- BOT_USERNAME: For deep link generation
- WEBHOOK_URL: Public endpoint for Telegram callbacks
- ADMIN_ID: Administrative user access
- DATABASE_URL: PostgreSQL connection string
- PORT: Server binding (default: 8080)

**Error Recovery**:
- Application starts even if database connection fails initially
- Bot initialization failures don't crash the app
- Graceful degradation in component failures

## External Dependencies

### Third-Party Services

**Telegram Bot API**:
- Core platform for user authentication and messaging
- Provides user identity (no separate auth system needed)
- WebApp SDK for mini app integration
- Deep linking and share functionality

**PostgreSQL Database**:
- Primary data store for all application data
- Can be hosted on Replit, Supabase, Neon, or any Postgres provider
- Requires DATABASE_URL connection string
- SSL/TLS support for secure connections

### Python Dependencies

**Core Framework**:
- `fastapi==0.104.1`: Web framework
- `uvicorn[standard]==0.24.0`: ASGI server
- `pydantic==2.5.0`: Data validation

**Telegram Integration**:
- `python-telegram-bot==20.7`: Bot framework
- `telegram`: Telegram API wrapper

**Database**:
- `asyncpg==0.29.0`: Async PostgreSQL driver

**Utilities**:
- `python-dotenv==1.0.0`: Environment variable management

### External APIs

**Telegram WebApp SDK**: 
- Loaded via CDN: `https://telegram.org/js/telegram-web-app.js`
- Provides user context and WebApp lifecycle management

**Canvas Confetti**:
- Loaded via CDN: `https://cdn.jsdelivr.net/npm/canvas-confetti@1.6.0/dist/confetti.browser.min.js`
- Celebration animations on rank-ups and achievements

### Infrastructure Requirements

**Minimum**:
- Python 3.12+ runtime
- PostgreSQL 12+ database
- HTTPS-enabled web server
- Public webhook endpoint

**Recommended**:
- 512MB RAM minimum
- Persistent storage for database
- CDN for static assets (optional)
- Monitoring/logging service (optional)