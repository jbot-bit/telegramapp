// Vouch Portal - Client-side JavaScript
// Handles all UI interactions, API calls, and Telegram WebApp integration

// Initialize Telegram WebApp
const tg = window.Telegram.WebApp;
tg.expand();
tg.ready();

// Global state
let currentUser = null;
let currentTab = 'profile';
let allUsers = [];
let currentFilter = 'all';
let currentCommunityView = 'activity';
let currentLeaderboardType = 'most_vouched';
let botUsername = 'VouchPortalBot'; // Default, will be fetched from API

// API Base URL
const API_BASE = window.location.origin;

// Initialize app on load
document.addEventListener('DOMContentLoaded', () => {
    initializeApp();
});

async function initializeApp() {
    try {
        showLoading(true);

        // Get user from Telegram WebApp - REQUIRED
        const telegramUser = tg.initDataUnsafe?.user;

        if (!telegramUser) {
            showLoading(false);
            document.getElementById('app').innerHTML = `
                <div style="padding: 40px; text-align: center;">
                    <h2>⚠️ Telegram Required</h2>
                    <p>This app must be opened through Telegram.</p>
                    <p>Please open it via the Telegram bot.</p>
                </div>
            `;
            return;
        }

        // Fetch bot info and user profile in parallel
        const [botInfoResponse, profileResponse] = await Promise.all([
            fetch(`${API_BASE}/api/bot-info`),
            fetch(`${API_BASE}/api/profile/${telegramUser.id}`)
        ]);

        if (botInfoResponse.ok) {
            const botInfo = await botInfoResponse.json();
            botUsername = botInfo.bot_username || 'VouchPortalBot';
        }

        if (!profileResponse.ok) {
            throw new Error(`Failed to load profile: ${profileResponse.status}`);
        }
        
        const data = await profileResponse.json();
        currentUser = data.user;

        // Fetch profile photo for current user
        fetchAndCacheProfilePhoto(currentUser.telegram_user_id);

        // Check if user is admin (get from environment or set dynamically)
        const adminElements = document.querySelectorAll('.admin-only');
        if (adminElements.length > 0) {
            // You can implement admin check here if needed
            // For now, hide admin sections by default
            adminElements.forEach(el => el.style.display = 'none');
        }

        // Setup UI
        setupEventListeners();
        updateHeaderBadge();
        loadProfileTab();

        showLoading(false);
    } catch (error) {
        console.error('Initialization error:', error);
        showLoading(false);
        document.getElementById('app').innerHTML = `
            <div style="padding: 40px; text-align: center;">
                <h2>❌ Error Loading App</h2>
                <p>${error.message}</p>
                <p>Please try again or contact support.</p>
            </div>
        `;
    }
}

// Event Listeners
function setupEventListeners() {
    // Tab switching
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            switchTab(e.target.dataset.tab);
        });
    });

    // Vouch form
    const vouchForm = document.getElementById('vouchForm');
    if (vouchForm) {
        vouchForm.addEventListener('submit', handleVouchSubmit);
    }

    // Character counter
    const vouchMessage = document.getElementById('vouchMessage');
    if (vouchMessage) {
        vouchMessage.addEventListener('input', updateCharCount);
    }
    
    // Vote buttons
    document.querySelectorAll('.vote-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            document.querySelectorAll('.vote-btn').forEach(b => b.classList.remove('active'));
            e.target.classList.add('active');
            document.getElementById('voteType').value = e.target.dataset.vote;
        });
    });

    // Profile buttons
    const requestVouchBtn = document.getElementById('requestVouchBtn');
    if (requestVouchBtn) {
        requestVouchBtn.addEventListener('click', handleRequestVouch);
    }

    const shareProfileBtn = document.getElementById('shareProfileBtn');
    if (shareProfileBtn) {
        shareProfileBtn.addEventListener('click', handleShareProfile);
    }

    // Community search
    const communitySearch = document.getElementById('communitySearch');
    if (communitySearch) {
        communitySearch.addEventListener('input', handleSearch);
    }

    // Community filters
    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
            e.target.classList.add('active');
            currentFilter = e.target.dataset.filter;
            filterCommunity();
        });
    });
    
    // Community view tabs
    document.querySelectorAll('.view-tab-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const viewType = e.target.dataset.view;
            currentCommunityView = viewType;
            
            // Update tab buttons
            document.querySelectorAll('.view-tab-btn').forEach(b => b.classList.remove('active'));
            e.target.classList.add('active');
            
            // Switch views
            document.querySelectorAll('.community-view').forEach(view => {
                view.style.display = 'none';
                view.classList.remove('active');
            });
            
            if (viewType === 'activity') {
                document.getElementById('activityView').style.display = 'block';
                document.getElementById('activityView').classList.add('active');
                loadActivityFeed();
            } else if (viewType === 'users') {
                document.getElementById('usersView').style.display = 'block';
                document.getElementById('usersView').classList.add('active');
                loadUsersView();
            } else if (viewType === 'leaderboards') {
                document.getElementById('leaderboardsView').style.display = 'block';
                document.getElementById('leaderboardsView').classList.add('active');
                loadLeaderboardsView();
            }
        });
    });
    
    // Leaderboard tabs
    document.querySelectorAll('.lb-tab-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const boardType = e.target.dataset.board;
            currentLeaderboardType = boardType;
            
            // Update tab buttons
            document.querySelectorAll('.lb-tab-btn').forEach(b => b.classList.remove('active'));
            e.target.classList.add('active');
            
            // Load leaderboard
            loadLeaderboard(boardType);
        });
    });
    
    // View toggle buttons
    document.querySelectorAll('.view-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            document.querySelectorAll('.view-btn').forEach(b => b.classList.remove('active'));
            e.target.classList.add('active');
            const view = e.target.dataset.view;
            const grid = document.getElementById('communityGrid');
            if (view === 'list') {
                grid.classList.add('list-view');
            } else {
                grid.classList.remove('list-view');
            }
        });
    });

    // Modal close
    const closeModal = document.querySelector('.close');
    if (closeModal) {
        closeModal.addEventListener('click', () => {
            document.getElementById('profileModal').classList.remove('active');
        });
    }
    
    // Edit Profile button
    const editProfileBtn = document.getElementById('editProfileBtn');
    if (editProfileBtn) {
        editProfileBtn.addEventListener('click', openEditProfileModal);
    }
    
    // Edit Profile Modal close
    const closeEditModal = document.getElementById('closeEditModal');
    if (closeEditModal) {
        closeEditModal.addEventListener('click', () => {
            document.getElementById('editProfileModal').classList.remove('active');
        });
    }
    
    // Edit Profile form
    const editProfileForm = document.getElementById('editProfileForm');
    if (editProfileForm) {
        editProfileForm.addEventListener('submit', handleProfileUpdate);
    }
    
    // Bio character counter
    const editBio = document.getElementById('editBio');
    if (editBio) {
        editBio.addEventListener('input', () => {
            document.getElementById('bioCharCount').textContent = editBio.value.length;
        });
    }
    
    // Share Modal close
    const closeShareModal = document.getElementById('closeShareModal');
    if (closeShareModal) {
        closeShareModal.addEventListener('click', () => {
            document.getElementById('shareModal').classList.remove('active');
        });
    }
    
    // Copy link button
    const copyLinkBtn = document.getElementById('copyLinkBtn');
    if (copyLinkBtn) {
        copyLinkBtn.addEventListener('click', copyShareLink);
    }
    
    // Telegram share button
    const telegramShareBtn = document.getElementById('telegramShareBtn');
    if (telegramShareBtn) {
        telegramShareBtn.addEventListener('click', shareOnTelegram);
    }
    
    // Edit Vouch Modal close
    const closeEditVouchModal = document.getElementById('closeEditVouchModal');
    if (closeEditVouchModal) {
        closeEditVouchModal.addEventListener('click', () => {
            document.getElementById('editVouchModal').classList.remove('active');
        });
    }
    
    // Edit Vouch form
    const editVouchForm = document.getElementById('editVouchForm');
    if (editVouchForm) {
        editVouchForm.addEventListener('submit', handleEditVouchSubmit);
    }
    
    // Edit vouch message character counter
    const editVouchMessage = document.getElementById('editVouchMessage');
    if (editVouchMessage) {
        editVouchMessage.addEventListener('input', () => {
            document.getElementById('editVouchCharCount').textContent = editVouchMessage.value.length;
        });
    }
    
    // Return vouch button in mutual vouch toast
    const returnVouchBtn = document.getElementById('returnVouchBtn');
    if (returnVouchBtn) {
        returnVouchBtn.addEventListener('click', handleReturnVouch);
    }

    // Check URL parameters for deep linking
    const urlParams = new URLSearchParams(window.location.search);
    const view = urlParams.get('view');
    const id = urlParams.get('id');

    if (view) {
        switchTab(view);
    }

    if (id && view === 'profile') {
        loadUserProfile(parseInt(id));
    }
}

// Tab Switching
function switchTab(tabName) {
    currentTab = tabName;

    // Update tab buttons
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.tab === tabName);
    });

    // Update tab content
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });

    const targetTab = document.getElementById(`${tabName}-tab`);
    if (targetTab) {
        targetTab.classList.add('active');
    }

    // Load tab data
    switch (tabName) {
        case 'profile':
            loadProfileTab();
            break;
        case 'vouch':
            loadVouchTab();
            break;
        case 'community':
            loadCommunityTab();
            break;
        case 'insights':
            loadInsightsTab();
            break;
    }
}

// Profile Tab
async function loadProfileTab() {
    if (!currentUser) return;

    try {
        const response = await fetch(`${API_BASE}/api/profile/${currentUser.telegram_user_id}`);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();

        // Update profile header
        document.getElementById('profileName').textContent = `@${currentUser.username || currentUser.first_name}`;

        const rankBadge = document.getElementById('profileRank');
        const rankEmoji = getRankEmoji(data.user.rank);
        const rankName = getRankName(data.user.rank);
        rankBadge.textContent = `${rankEmoji} ${rankName}`;
        rankBadge.className = `rank-badge ${data.user.rank}`;
        
        // Update bio if exists
        if (data.user.bio) {
            document.getElementById('bioText').textContent = data.user.bio;
            document.getElementById('profileBio').style.display = 'block';
        } else {
            document.getElementById('profileBio').style.display = 'none';
        }
        
        // Update location if exists
        if (data.user.location) {
            document.getElementById('locationText').textContent = data.user.location;
            document.getElementById('profileLocation').style.display = 'block';
        } else {
            document.getElementById('profileLocation').style.display = 'none';
        }

        // Update stats
        const positiveVotes = data.user.positive_votes || 0;
        const negativeVotes = data.user.negative_votes || 0;
        const ratingPercentage = data.user.rating_percentage || 100;
        
        document.getElementById('positiveVotes').textContent = positiveVotes;
        document.getElementById('negativeVotes').textContent = negativeVotes;
        
        // Update rating display
        const ratingDisplay = document.getElementById('ratingDisplay');
        const ratingPercentageEl = ratingDisplay.querySelector('.rating-percentage');
        ratingPercentageEl.textContent = `${Math.round(ratingPercentage)}%`;
        
        // Color code the rating
        if (ratingPercentage >= 80) {
            ratingDisplay.className = 'rating-display rating-high';
        } else if (ratingPercentage >= 60) {
            ratingDisplay.className = 'rating-display rating-medium';
        } else {
            ratingDisplay.className = 'rating-display rating-low';
        }
        
        // Update streak
        const streakDays = data.user.streak_days || 0;
        const streakElement = document.getElementById('streakCount');
        if (streakDays > 0) {
            streakElement.textContent = `🔥 ${streakDays}`;
            streakElement.parentElement.classList.add('active-streak');
        } else {
            streakElement.textContent = '0';
            streakElement.parentElement.classList.remove('active-streak');
        }

        // Update progress
        updateProgressBar(data.user.total_vouches, data.next_rank_threshold, data.progress_percentage);

        // Render vouches
        renderVouches('receivedVouches', data.vouches_received);
        renderVouches('givenVouches', data.vouches_given, true); // true = show edit button
    } catch (error) {
        console.error('Error loading profile:', error);
        showToast('Failed to load profile data', 'error');
    }
}

function updateProgressBar(current, next, percentage) {
    // Handle max rank achieved (strictly null or undefined, not 0)
    if (next == null) {
        document.getElementById('progressText').textContent = '👑 Max rank achieved!';
        document.getElementById('progressFill').style.width = '100%';
        
        // Remove pulse effect for max rank users
        const requestBtn = document.getElementById('requestVouchBtn');
        if (requestBtn) {
            requestBtn.classList.remove('pulse');
        }
        return;
    }
    
    const remaining = next - current;
    let progressText = `${current}/${next}`;
    
    // Add progress pressure message if close to next rank
    if (remaining > 0 && remaining <= 3) {
        progressText = `Only ${remaining} to reach next rank!`;
    }
    
    document.getElementById('progressText').textContent = progressText;
    document.getElementById('progressFill').style.width = `${percentage}%`;
    
    // Add/remove pulse effect on Request Vouch button based on verification status
    const requestBtn = document.getElementById('requestVouchBtn');
    if (requestBtn && current < 3) {
        requestBtn.classList.add('pulse');
    } else if (requestBtn) {
        requestBtn.classList.remove('pulse');
    }
}

function renderVouches(containerId, vouches, showEditButton = false) {
    const container = document.getElementById(containerId);

    if (!vouches || vouches.length === 0) {
        container.innerHTML = '<div class="empty-state">No vouches yet</div>';
        return;
    }

    container.innerHTML = vouches.map(vouch => {
        const isPending = vouch.is_pending || !vouch.username;
        const displayName = isPending ? `@${vouch.to_username}` : `@${vouch.username || vouch.first_name}`;
        const statusBadge = isPending ? '<span style="color: #888; font-size: 11px;">⏳ Pending</span>' : '';
        const canEdit = showEditButton && currentUser && vouch.from_user_id === currentUser.telegram_user_id;
        const editedBadge = vouch.updated_at ? '<span style="color: #888; font-size: 11px; margin-left: 8px;">(edited)</span>' : '';
        
        return `
        <div class="vouch-item ${isPending ? 'pending' : ''}" data-vouch-id="${vouch.id}">
            <div class="vouch-header">
                <span class="vouch-user">${displayName}</span>
                <span class="vouch-date">${formatDate(vouch.created_at)}${editedBadge}</span>
            </div>
            ${statusBadge ? `<div style="margin-top: 4px;">${statusBadge}</div>` : ''}
            ${vouch.message ? `<div class="vouch-message">"${vouch.message}"</div>` : ''}
            ${canEdit ? `<button class="btn-edit" onclick="openEditVouchModal(${vouch.id}, '${(vouch.message || '').replace(/'/g, "\\'")}')">✏️ Edit</button>` : ''}
        </div>
        `;
    }).join('');
}

// Vouch Tab
async function loadVouchTab() {
    if (!currentUser) return;

    try {
        const response = await fetch(`${API_BASE}/api/profile/${currentUser.telegram_user_id}`);
        const data = await response.json();

        // Show recent vouches given
        renderRecentVouches(data.vouches_given.slice(0, 5));
    } catch (error) {
        console.error('Error loading vouch tab:', error);
    }
}

function renderRecentVouches(vouches) {
    const container = document.getElementById('recentVouches');

    if (!vouches || vouches.length === 0) {
        container.innerHTML = '<div class="empty-state">No recent vouches</div>';
        return;
    }

    container.innerHTML = vouches.map(vouch => {
        const isPending = vouch.is_pending || !vouch.username;
        const displayName = isPending ? `@${vouch.to_username}` : `@${vouch.username || vouch.first_name}`;
        const statusBadge = isPending ? '<span style="color: #888; font-size: 11px;">⏳ Pending</span>' : '';
        const editedBadge = vouch.updated_at ? '<span style="color: #888; font-size: 11px; margin-left: 8px;">(edited)</span>' : '';
        
        return `
        <div class="vouch-item ${isPending ? 'pending' : ''}" data-vouch-id="${vouch.id}">
            <div class="vouch-header">
                <span class="vouch-user">${displayName}</span>
                <span class="vouch-date">${formatDate(vouch.created_at)}${editedBadge}</span>
            </div>
            ${statusBadge ? `<div style="margin-top: 4px;">${statusBadge}</div>` : ''}
            ${vouch.message ? `<div class="vouch-message">"${vouch.message}"</div>` : ''}
            <button class="btn-edit" onclick="openEditVouchModal(${vouch.id}, '${(vouch.message || '').replace(/'/g, "\\'")}')">✏️ Edit</button>
        </div>
        `;
    }).join('');
}

async function handleVouchSubmit(e) {
    e.preventDefault();

    const targetUsername = document.getElementById('targetUsername').value.trim();
    const message = document.getElementById('vouchMessage').value.trim();

    if (!targetUsername) {
        showToast('Please enter a username', 'error');
        return;
    }

    try {
        showLoading(true);

        const voteType = document.getElementById('voteType').value;
        
        const response = await fetch(`${API_BASE}/api/vouch`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                from_user_id: currentUser.telegram_user_id,
                to_username: targetUsername,
                message: message || null,
                vote_type: voteType
            })
        });

        const data = await response.json();

        if (response.ok) {
            // Check if vouch is pending or confirmed
            if (data.pending) {
                // Pending vouch - user hasn't joined yet
                showToast(`⏳ Vouch saved for @${targetUsername}! They'll receive it when they join the bot.`, 'info');
                
                // Smaller confetti for pending
                confetti({
                    particleCount: 50,
                    spread: 50,
                    origin: { y: 0.6 }
                });
            } else {
                // Confirmed vouch - user exists
                showToast('✅ Vouch recorded successfully!', 'success');
                
                // Trigger confetti
                confetti({
                    particleCount: 100,
                    spread: 70,
                    origin: { y: 0.6 }
                });
                
                // Check for mutual vouch
                if (data.mutual_vouch) {
                    setTimeout(() => {
                        showMutualVouchPrompt(targetUsername);
                    }, 2000);
                }
            }

            // Vibrate if supported
            if (tg.HapticFeedback) {
                tg.HapticFeedback.notificationOccurred('success');
            }

            // Reset form
            document.getElementById('vouchForm').reset();
            updateCharCount();

            // Reload vouch tab
            loadVouchTab();
        } else {
            showToast(data.detail || 'Failed to submit vouch', 'error');
        }

        showLoading(false);
    } catch (error) {
        console.error('Error submitting vouch:', error);
        showToast('Failed to submit vouch', 'error');
        showLoading(false);
    }
}

function showMutualVouchPrompt(username) {
    showToast(`💬 @${username} also vouched for you! Return the favor?`, 'success');
}

function updateCharCount() {
    const textarea = document.getElementById('vouchMessage');
    const counter = document.getElementById('charCount');
    if (textarea && counter) {
        counter.textContent = textarea.value.length;
    }
}

// Community Tab
async function loadCommunityTab() {
    // Load based on current view
    if (currentCommunityView === 'activity') {
        await loadActivityFeed();
    } else if (currentCommunityView === 'users') {
        await loadUsersView();
    } else if (currentCommunityView === 'leaderboards') {
        await loadLeaderboardsView();
    }
}

async function loadActivityFeed() {
    try {
        showLoading(true);
        const response = await fetch(`${API_BASE}/api/activity?limit=50`);
        
        if (!response.ok) {
            throw new Error(`Failed to load activity: ${response.status}`);
        }
        
        const data = await response.json();
        renderActivityFeed(data.activity);
        showLoading(false);
    } catch (error) {
        console.error('Error loading activity:', error);
        showToast('Failed to load activity feed', 'error');
        showLoading(false);
    }
}

function renderActivityFeed(activities) {
    const container = document.getElementById('activityFeed');
    
    if (!activities || activities.length === 0) {
        container.innerHTML = '<div class="empty-state">No recent activity</div>';
        return;
    }
    
    container.innerHTML = activities.map(activity => {
        if (activity.activity_type === 'vouch') {
            const fromName = activity.from_username || activity.from_first_name;
            const toName = activity.to_username || activity.to_first_name;
            return `
                <div class="activity-item">
                    <div class="activity-icon">💬</div>
                    <div class="activity-content">
                        <div class="activity-text">
                            <strong>@${fromName}</strong> vouched for <strong>@${toName}</strong>
                        </div>
                        ${activity.message ? `<div class="activity-message">"${activity.message}"</div>` : ''}
                        <div class="activity-time">${formatDate(activity.created_at)}</div>
                    </div>
                </div>
            `;
        } else if (activity.activity_type === 'rank_up') {
            const name = activity.username || activity.first_name;
            const newRankEmoji = getRankEmoji(activity.new_rank);
            const newRankName = getRankName(activity.new_rank);
            return `
                <div class="activity-item rank-up">
                    <div class="activity-icon">🎉</div>
                    <div class="activity-content">
                        <div class="activity-text">
                            <strong>@${name}</strong> reached <strong>${newRankEmoji} ${newRankName}</strong>
                        </div>
                        <div class="activity-time">${formatDate(activity.created_at)}</div>
                    </div>
                </div>
            `;
        }
        return '';
    }).join('');
}

async function loadUsersView() {
    try {
        showLoading(true);
        const response = await fetch(`${API_BASE}/api/users?limit=100`);
        
        if (!response.ok) {
            throw new Error(`Failed to load users: ${response.status}`);
        }
        
        const data = await response.json();
        allUsers = data.users;
        renderCommunityGrid(allUsers);
        showLoading(false);
    } catch (error) {
        console.error('Error loading users:', error);
        showToast('Failed to load users', 'error');
        showLoading(false);
    }
}

async function loadLeaderboardsView() {
    await loadLeaderboard(currentLeaderboardType);
}

async function loadLeaderboard(boardType) {
    try {
        showLoading(true);
        const response = await fetch(`${API_BASE}/api/leaderboards/${boardType}?limit=20`);
        
        if (!response.ok) {
            throw new Error(`Failed to load leaderboard: ${response.status}`);
        }
        
        const data = await response.json();
        renderLeaderboard(data.leaderboard, boardType);
        showLoading(false);
    } catch (error) {
        console.error('Error loading leaderboard:', error);
        showToast('Failed to load leaderboard', 'error');
        showLoading(false);
    }
}

function renderLeaderboard(users, boardType) {
    const container = document.getElementById('leaderboardContent');
    
    if (!users || users.length === 0) {
        container.innerHTML = '<div class="empty-state">No data available</div>';
        return;
    }
    
    container.innerHTML = users.map((user, index) => {
        const medals = ['🥇', '🥈', '🥉'];
        const medal = index < 3 ? medals[index] : `${index + 1}.`;
        const name = user.username || user.first_name;
        
        let extraStat = '';
        if (boardType === 'top_givers' && user.vouches_given !== undefined) {
            extraStat = `${user.vouches_given} given`;
        } else if (boardType === 'rising_stars' && user.recent_vouches !== undefined) {
            extraStat = `+${user.recent_vouches} this week`;
        } else if (boardType === 'streak_leaders') {
            extraStat = `🔥 ${user.streak_days} days`;
        } else {
            extraStat = `${user.total_vouches} vouches`;
        }
        
        const photoHTML = user.profile_picture_url 
            ? `<div class="lb-avatar" style="background-image: url(${API_BASE}/api/photo-proxy/${user.profile_picture_url}); background-size: cover; background-position: center; width: 32px; height: 32px; border-radius: 50%; margin-right: 12px;"></div>`
            : `<div class="lb-avatar" style="width: 32px; height: 32px; border-radius: 50%; background: var(--bg-secondary); display: flex; align-items: center; justify-content: center; margin-right: 12px; font-size: 16px;">👤</div>`;
        
        return `
            <div class="leaderboard-item" onclick="loadUserProfile(${user.telegram_user_id})" style="display: flex; align-items: center;">
                <div class="lb-position">${medal}</div>
                ${photoHTML}
                <div class="lb-info">
                    <div class="lb-name">@${name}</div>
                    <div class="lb-stat">${user.rank_emoji} ${user.rank_name} • ${extraStat}</div>
                </div>
            </div>
        `;
    }).join('');
}

function renderCommunityGrid(users) {
    const container = document.getElementById('communityGrid');

    if (!users || users.length === 0) {
        container.innerHTML = '<div class="empty-state">No users found</div>';
        return;
    }

    container.innerHTML = users.map(user => {
        const photoHTML = user.profile_picture_url 
            ? `<div class="community-avatar" style="background-image: url(${API_BASE}/api/photo-proxy/${user.profile_picture_url}); background-size: cover; background-position: center;"></div>`
            : `<div class="community-avatar">👤</div>`;
        
        return `
            <div class="community-card" onclick="loadUserProfile(${user.telegram_user_id})">
                ${photoHTML}
                <div class="community-name">@${user.username || user.first_name}</div>
                <div class="community-rank">${user.rank_emoji} ${user.rank_name}</div>
                <div class="community-vouches">${user.total_vouches} vouches</div>
            </div>
        `;
    }).join('');
}

function filterCommunity() {
    if (currentFilter === 'all') {
        renderCommunityGrid(allUsers);
        return;
    }

    const filtered = allUsers.filter(user => user.rank === currentFilter);
    renderCommunityGrid(filtered);
}

async function handleSearch(e) {
    const query = e.target.value.trim();

    if (query.length < 2) {
        renderCommunityGrid(allUsers);
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/api/search?q=${encodeURIComponent(query)}`);
        const data = await response.json();

        renderCommunityGrid(data.users);
    } catch (error) {
        console.error('Search error:', error);
    }
}

async function loadUserProfile(userId) {
    try {
        showLoading(true);

        const response = await fetch(`${API_BASE}/api/profile/${userId}`);
        const data = await response.json();

        // Fetch profile photo file_id if not cached
        if (!data.user.profile_picture_url) {
            await fetchAndCacheProfilePhoto(userId);
        }

        const modal = document.getElementById('profileModal');
        const content = document.getElementById('modalProfileContent');

        const rankEmoji = getRankEmoji(data.user.rank);
        const rankName = getRankName(data.user.rank);

        content.innerHTML = `
            <div class="profile-header">
                ${getProfilePhotoHTML(data.user)}
                <div class="profile-info">
                    <h2>@${data.user.username || data.user.first_name}</h2>
                    <div class="rank-badge ${data.user.rank}">${rankEmoji} ${rankName}</div>
                    ${data.user.streak_days > 0 ? `<div class="streak-badge">🔥 ${data.user.streak_days} day streak</div>` : ''}
                </div>
            </div>

            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-value">${data.user.total_vouches}</div>
                    <div class="stat-label">Vouches</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">${data.vouches_given.length}</div>
                    <div class="stat-label">Given</div>
                </div>
                ${data.user.streak_days > 0 ? `
                <div class="stat-card streak-card active-streak">
                    <div class="stat-value">🔥 ${data.user.streak_days}</div>
                    <div class="stat-label">Day Streak</div>
                </div>
                ` : ''}
            </div>

            <button class="btn btn-primary btn-large" onclick="vouchUser('${data.user.username || data.user.first_name}')">
                👍 Vouch for this user
            </button>

            <div class="section">
                <h3>Recent Vouches</h3>
                ${data.vouches_received.slice(0, 5).map(vouch => `
                    <div class="vouch-item">
                        <div class="vouch-header">
                            <span class="vouch-user">@${vouch.username || vouch.first_name}</span>
                            <span class="vouch-date">${formatDate(vouch.created_at)}</span>
                        </div>
                        ${vouch.message ? `<div class="vouch-message">"${vouch.message}"</div>` : ''}
                    </div>
                `).join('') || '<div class="empty-state">No vouches yet</div>'}
            </div>
        `;

        modal.classList.add('active');
        showLoading(false);
    } catch (error) {
        console.error('Error loading user profile:', error);
        showToast('Failed to load profile', 'error');
        showLoading(false);
    }
}

function vouchUser(username) {
    document.getElementById('profileModal').classList.remove('active');
    switchTab('vouch');
    document.getElementById('targetUsername').value = username;
    document.getElementById('targetUsername').focus();
}

// Insights Tab (Admin)
async function loadInsightsTab() {
    try {
        showLoading(true);

        const response = await fetch(`${API_BASE}/api/analytics`);
        const data = await response.json();

        // Update overview stats
        document.getElementById('totalUsers').textContent = data.total_users;
        document.getElementById('activeUsers24h').textContent = data.active_users['24h'];
        document.getElementById('totalVouches').textContent = data.total_vouches;
        document.getElementById('newSignups').textContent = data.new_signups_7d;

        // Render rank distribution
        renderRankDistribution(data.rank_distribution);

        // Render leaderboards
        renderLeaderboard('topHelpers', data.top_helpers);
        renderLeaderboard('mostVouched', data.most_vouched);

        showLoading(false);
    } catch (error) {
        console.error('Error loading insights:', error);
        showToast('Failed to load analytics', 'error');
        showLoading(false);
    }
}

function renderRankDistribution(distribution) {
    const container = document.getElementById('rankDistribution');
    const total = distribution.reduce((sum, item) => sum + item.count, 0);

    container.innerHTML = distribution.map(item => {
        const percentage = (item.count / total * 100).toFixed(1);
        const emoji = getRankEmoji(item.rank);
        const name = getRankName(item.rank);

        return `
            <div class="rank-chart-item">
                <span style="min-width: 120px;">${emoji} ${name}</span>
                <div class="rank-chart-bar" style="flex: 1;">
                    <div class="rank-chart-fill" style="width: ${percentage}%"></div>
                </div>
                <span style="min-width: 60px; text-align: right;">${item.count} (${percentage}%)</span>
            </div>
        `;
    }).join('');
}

function renderLeaderboard(containerId, users) {
    const container = document.getElementById(containerId);

    if (!users || users.length === 0) {
        container.innerHTML = '<div class="empty-state">No data yet</div>';
        return;
    }

    container.innerHTML = users.map((user, index) => {
        const emoji = index === 0 ? '🥇' : index === 1 ? '🥈' : index === 2 ? '🥉' : `${index + 1}.`;
        const value = user.vouch_count || user.total_vouches;

        return `
            <div class="leaderboard-item">
                <span class="leaderboard-rank">${emoji}</span>
                <div class="leaderboard-info">
                    <div class="leaderboard-name">@${user.username || user.first_name}</div>
                </div>
                <span class="leaderboard-value">${value}</span>
            </div>
        `;
    }).join('');
}

// Profile photo helpers
async function fetchAndCacheProfilePhoto(userId) {
    try {
        const response = await fetch(`${API_BASE}/api/profile-photo/${userId}`);
        if (response.ok) {
            const data = await response.json();
            if (data.success && data.file_id) {
                // Construct secure proxy URL
                const proxyUrl = `${API_BASE}/api/photo-proxy/${data.file_id}`;
                
                // Update currentUser if it's their photo
                if (currentUser && currentUser.telegram_user_id === userId) {
                    currentUser.profile_photo_proxy_url = proxyUrl;
                    updateProfilePhoto();
                }
                return proxyUrl;
            }
        }
    } catch (error) {
        console.error(`Failed to fetch profile photo for user ${userId}:`, error);
    }
    return null;
}

function updateProfilePhoto() {
    const avatarElements = document.querySelectorAll('.avatar');
    avatarElements.forEach(el => {
        if (currentUser && currentUser.profile_photo_proxy_url) {
            el.style.backgroundImage = `url(${currentUser.profile_photo_proxy_url})`;
            el.style.backgroundSize = 'cover';
            el.style.backgroundPosition = 'center';
            el.textContent = '';
        }
    });
}

function getProfilePhotoHTML(user) {
    if (user && user.profile_picture_url) {
        // profile_picture_url contains file_id, construct proxy URL
        const proxyUrl = `${API_BASE}/api/photo-proxy/${user.profile_picture_url}`;
        return `<div class="avatar" style="background-image: url(${proxyUrl}); background-size: cover; background-position: center;"></div>`;
    }
    return `<div class="avatar">👤</div>`;
}

// Profile Actions
async function handleRequestVouch() {
    const shareUrl = `https://t.me/${botUsername}?startapp=profile_${currentUser.telegram_user_id}`;

    if (tg.isVersionAtLeast('6.1')) {
        tg.openTelegramLink(`https://t.me/share/url?url=${encodeURIComponent(shareUrl)}&text=${encodeURIComponent('Please vouch for me on Vouch Portal!')}`);
    } else {
        // Fallback: copy to clipboard
        await navigator.clipboard.writeText(shareUrl);
        showToast('Link copied to clipboard!', 'success');
    }

    // Log event
    await fetch(`${API_BASE}/api/share`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            user_id: currentUser.telegram_user_id,
            platform: 'telegram'
        })
    });
}

async function handleShareProfile() {
    const rankEmoji = getRankEmoji(currentUser.rank);
    const rankName = getRankName(currentUser.rank);
    const shareText = `I just reached ${rankEmoji} ${rankName} on Vouch Portal! Build yours: https://t.me/VouchPortalBot?startapp=ref_${currentUser.telegram_user_id}`;

    if (tg.isVersionAtLeast('6.1')) {
        tg.openTelegramLink(`https://t.me/share/url?text=${encodeURIComponent(shareText)}`);
    } else {
        await navigator.clipboard.writeText(shareText);
        showToast('Share text copied to clipboard!', 'success');
    }

    // Log event
    await fetch(`${API_BASE}/api/share`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            user_id: currentUser.telegram_user_id,
            platform: 'share'
        })
    });
}

// Header Badge
function updateHeaderBadge() {
    if (!currentUser) return;

    const badge = document.getElementById('userBadge');
    const emoji = getRankEmoji(currentUser.rank);
    badge.textContent = `${emoji} ${currentUser.total_vouches} vouches`;
}

// Utility Functions
function getRankEmoji(rank) {
    const emojis = {
        'unverified': '🚫',
        'verified': '✅',
        'trusted': '🔷',
        'endorsed': '🛡',
        'top_tier': '👑'
    };
    return emojis[rank] || '❓';
}

function getRankName(rank) {
    const names = {
        'unverified': 'Unverified',
        'verified': 'Verified',
        'trusted': 'Trusted',
        'endorsed': 'Endorsed',
        'top_tier': 'Top-Tier'
    };
    return names[rank] || 'Unknown';
}

function formatDate(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;

    return date.toLocaleDateString();
}

function showToast(message, type = 'success') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = `toast ${type} show`;

    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}

function showLoading(show) {
    const overlay = document.getElementById('loadingOverlay');
    if (show) {
        overlay.classList.add('active');
    } else {
        overlay.classList.remove('active');
    }
}

// Profile Editing
async function openEditProfileModal() {
    try {
        // Fetch current profile
        const response = await fetch(`${API_BASE}/api/profile/${currentUser.telegram_user_id}`);
        const data = await response.json();
        
        // Populate form with current values
        document.getElementById('editBio').value = data.user.bio || '';
        document.getElementById('editLocation').value = data.user.location || '';
        document.getElementById('bioCharCount').textContent = (data.user.bio || '').length;
        
        // Show modal
        document.getElementById('editProfileModal').classList.add('active');
    } catch (error) {
        console.error('Error opening edit profile:', error);
        showToast('Failed to load profile for editing', 'error');
    }
}

async function handleProfileUpdate(e) {
    e.preventDefault();
    
    const bio = document.getElementById('editBio').value.trim();
    const location = document.getElementById('editLocation').value.trim();
    
    try {
        showLoading(true);
        
        const response = await fetch(`${API_BASE}/api/profile/update`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                user_id: currentUser.telegram_user_id,
                bio: bio || null,
                location: location || null
            })
        });
        
        if (response.ok) {
            showToast('✅ Profile updated successfully!', 'success');
            document.getElementById('editProfileModal').classList.remove('active');
            
            // Reload profile tab
            await loadProfileTab();
        } else {
            const error = await response.json();
            showToast(error.detail || 'Failed to update profile', 'error');
        }
    } catch (error) {
        console.error('Error updating profile:', error);
        showToast('Failed to update profile', 'error');
    } finally {
        showLoading(false);
    }
}

// Edit Vouch functionality
let currentEditVouchId = null;

function openEditVouchModal(vouchId, currentMessage) {
    currentEditVouchId = vouchId;
    
    // Populate form with current message
    const textarea = document.getElementById('editVouchMessage');
    textarea.value = currentMessage || '';
    document.getElementById('editVouchCharCount').textContent = currentMessage.length;
    
    // Show modal
    document.getElementById('editVouchModal').classList.add('active');
}

async function handleEditVouchSubmit(e) {
    e.preventDefault();
    
    if (!currentEditVouchId) {
        showToast('Error: No vouch selected', 'error');
        return;
    }
    
    const message = document.getElementById('editVouchMessage').value.trim();
    
    try {
        showLoading(true);
        
        const response = await fetch(`${API_BASE}/api/vouches/${currentEditVouchId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                from_user_id: currentUser.telegram_user_id,
                message: message
            })
        });
        
        if (response.ok) {
            showToast('✅ Vouch updated successfully!', 'success');
            document.getElementById('editVouchModal').classList.remove('active');
            
            // Reload the current tab to show updated vouch
            if (currentTab === 'profile') {
                await loadProfileTab();
            } else if (currentTab === 'vouch') {
                await loadVouchTab();
            }
            
            currentEditVouchId = null;
        } else {
            const error = await response.json();
            showToast(error.detail || 'Failed to update vouch', 'error');
        }
    } catch (error) {
        console.error('Error updating vouch:', error);
        showToast('Failed to update vouch', 'error');
    } finally {
        showLoading(false);
    }
}

// Handle visibility change (refresh data when tab becomes visible)
document.addEventListener('visibilitychange', () => {
    if (!document.hidden && currentUser) {
        loadProfileTab();
    }
});

// Share Modal Functions
async function copyShareLink() {
    const shareLink = document.getElementById('shareLink').value;
    try {
        await navigator.clipboard.writeText(shareLink);
        showToast('✅ Link copied to clipboard!', 'success');
    } catch (error) {
        console.error('Error copying link:', error);
        showToast('Failed to copy link', 'error');
    }
}

function shareOnTelegram() {
    const modal = document.getElementById('shareModal');
    const shareText = modal.dataset.shareText;
    const shareLink = modal.dataset.shareLink;
    
    if (tg.isVersionAtLeast && tg.isVersionAtLeast('6.1')) {
        tg.openTelegramLink(`https://t.me/share/url?url=${encodeURIComponent(shareLink)}&text=${encodeURIComponent(shareText)}`);
    } else {
        tg.openLink(`https://t.me/share/url?url=${encodeURIComponent(shareLink)}&text=${encodeURIComponent(shareText)}`);
    }
    
    modal.classList.remove('active');
}

// Mutual Vouch CTA
let mutualVouchUsername = null;

function showMutualVouchCTA(username) {
    mutualVouchUsername = username;
    document.getElementById('mutualVouchMessage').textContent = `💬 @${username} vouched for you! Return the favor?`;
    
    const toast = document.getElementById('mutualVouchToast');
    toast.classList.add('show');
    
    setTimeout(() => {
        toast.classList.remove('show');
    }, 8000);
}

function handleReturnVouch() {
    if (mutualVouchUsername) {
        document.getElementById('mutualVouchToast').classList.remove('active');
        switchTab('vouch');
        document.getElementById('targetUsername').value = mutualVouchUsername;
        document.getElementById('targetUsername').focus();
        mutualVouchUsername = null;
    }
}

// Telegram WebApp theme
if (tg.colorScheme === 'dark') {
    document.body.classList.add('dark-theme');
}
