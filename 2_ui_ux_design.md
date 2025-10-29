# VOUCH PORTAL — UI/UX & USER EXPERIENCE DESIGN (Claude Instruction Set 2 of 4)

## OBJECTIVE
Design a **clean, mobile-first web interface** that feels like a native Telegram experience.
Focus on minimal friction, instant feedback, and strong community psychology (trust, reciprocity, progress).

---

## CORE UX PRINCIPLES

- **Simplicity:** 1-tap actions, no clutter, no forms.
- **Feedback:** Micro-animations and confetti for every user action.
- **Continuity:** Everything flows through Telegram identity — no signups or passwords.
- **Safety:** All user-generated content auto-sanitized.
- **Trust tone:** Neutral, positive language. Never accusatory or negative.

---

## PAGE STRUCTURE

### 1️⃣ HOME PAGE (`/`)
- Header: “🤝 Vouch Portal”
- Tabs:
  - **My Profile**
  - **Vouch Someone**
  - **Community**
  - **Insights (Admin only)**
- Persistent footer with badge + rank progress bar

---

### 2️⃣ MY PROFILE TAB
Shows:
- Avatar (`tg://userpic`)
- Username
- Rank + emoji
- Vouch count and streak
- “Request Vouch” button → Opens modal with invite link
- “Received Vouches” list (scrollable cards)

If unverified: gray theme, “🚫 Not Yet Verified”
If verified: green/blue accent per rank.

---

### 3️⃣ VOUCH SOMEONE TAB
- Input: `@username`
- Optional message box (auto-trims, 120 chars)
- AI-scan message for banned words → replaces with `[redacted]`
- Submit button → animated ✅ “Vouch Recorded”
- Below: mini-list of last 5 people you vouched for

---

### 4️⃣ COMMUNITY TAB
- Search bar (filter by username or rank)
- Directory grid with:
  - Avatar
  - Username
  - Rank emoji
  - Vouch count
- Tap = opens profile overlay (shows all vouches & comments)

---

### 5️⃣ INSIGHTS TAB (ADMIN)
- Metrics (DAU, total vouches, rank distribution)
- “Top Helpers This Week”
- “Recent Joins”
- “Health Status” indicators (green/red)

---

## COLOR SCHEME
| Theme | Color | Use |
|--------|--------|------|
| Background | #0f141a | dark mode base |
| Accent | #2AABEE | Telegram blue |
| Verified | #4CAF50 | success green |
| Warning | #FFB300 | amber |
| Error | #F44336 | red |
| Text | #E0E0E0 | readable gray |

Typography: system font stack (SF Pro, Roboto, Segoe UI)

---

## VISUAL ELEMENTS
- **Rank Badges** (SVG icons or PNG):
  - 🚫 Unverified → gray outline
  - ✅ Verified → green check
  - 🔷 Trusted → blue diamond
  - 🛡 Endorsed → silver shield
  - 👑 Top-Tier → gold crown
- **Animated Progress Bar:** fills as vouches increase
- **Confetti Animation:** plays when rank upgrades
- **Pulse effect** on “Request Vouch” button if unverified

---

## USER EMOTION STRATEGY

### Positive Triggers
- “Your trust score just increased!”
- “You’re now 🔷 Trusted — people believe in you.”
- “Someone vouched for you 👀 Tap to see!”

### Avoid
- “Untrusted”, “Report”, “Scam”, “Review”, “Rating”

---

## MICROCOPY & DISCLAIMERS

#### Inline Disclaimer (always visible under vouch text box):
> ⚠️ All feedback is community-based and non-verifiable.  
> Keep comments respectful — inappropriate language is filtered automatically.

#### Profile Footer
> This app promotes peer-based trust.  
> Do not rely on it for financial or legal verification.

---

## UI BEHAVIOR
- All button clicks → visual press feedback
- Modal close → fade transition
- New vouch received → gentle “slide down” toast
- Rank-up → confetti + short vibration

---

## RESPONSIVE DESIGN
- Full-width cards on mobile
- 3-column grid on desktop
- 100% touch-friendly
- No horizontal scrolling
- Font auto-scales

---

## IMPLEMENTATION REQUEST
Claude should generate:
1. `/webapp/index.html` (core layout, tabs)
2. `/webapp/static/styles.css` (lightweight Tailwind-style or inline CSS)
3. `/webapp/static/main.js` (handle tab switching, animations, API calls)
4. JSON config for rank emojis + color codes
5. Accessible version (text contrast + aria labels)

---

End of `2_ui_ux_design.md`
