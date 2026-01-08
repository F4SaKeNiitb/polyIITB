/**
 * Markets Module
 * Handles market listing, filtering, and display
 */

let allMarkets = [];
let currentFilter = 'all';

async function loadMarkets() {
    const grid = document.getElementById('markets-grid');
    grid.innerHTML = `
        <div class="loading-spinner">
            <div class="spinner"></div>
            <p>Loading markets...</p>
        </div>
    `;

    try {
        const response = await fetch(`${API_BASE}/markets`);
        if (!response.ok) throw new Error('Failed to load markets');

        allMarkets = await response.json();
        renderMarkets();
        loadMarketStats();
    } catch (error) {
        console.error('Error loading markets:', error);
        grid.innerHTML = `
            <div class="empty-state">
                <p>Failed to load markets. Please try again later.</p>
            </div>
        `;
    }
}

function renderMarkets() {
    const grid = document.getElementById('markets-grid');

    let filteredMarkets = allMarkets;
    if (currentFilter !== 'all') {
        filteredMarkets = allMarkets.filter(m => m.category === currentFilter);
    }

    if (filteredMarkets.length === 0) {
        grid.innerHTML = `
            <div class="empty-state">
                <p>No markets found${currentFilter !== 'all' ? ` in ${escapeHtml(currentFilter)}` : ''}.</p>
            </div>
        `;
        return;
    }

    grid.innerHTML = filteredMarkets.map(market => createMarketCard(market)).join('');
}

function createMarketCard(market) {
    const yesPercent = Math.round(market.yes_price * 100);
    const noPercent = Math.round(market.no_price * 100);

    return `
        <div class="market-card" onclick="openMarketDetail(${market.id})">
            <div class="market-card-header">
                <span class="market-category">${escapeHtml(market.category)}</span>
                <span class="market-volume">Vol: 🪙${formatNumber(market.total_volume)}</span>
            </div>
            <h3 class="market-title">${escapeHtml(market.title)}</h3>
            <div class="market-prices">
                <div class="price-box yes">
                    <span class="price-label">Yes</span>
                    <span class="price-value">${yesPercent}</span>
                </div>
                <div class="price-box no">
                    <span class="price-label">No</span>
                    <span class="price-value">${noPercent}</span>
                </div>
            </div>
        </div>
    `;
}

async function loadMarketStats() {
    try {
        const response = await fetch(`${API_BASE}/markets/stats`);
        if (response.ok) {
            const stats = await response.json();
            document.getElementById('stat-markets').textContent = stats.open_markets;
            document.getElementById('stat-volume').textContent = `🪙${formatNumber(stats.total_volume)}`;
        }
    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

// Market detail modal
let currentMarket = null;
let currentUserPosition = null;
let currentMarketOrders = [];

async function openMarketDetail(marketId) {
    const modal = document.getElementById('market-modal');
    const detail = document.getElementById('market-detail');

    modal.classList.add('show');
    detail.innerHTML = `
        <div class="loading-spinner">
            <div class="spinner"></div>
            <p>Loading market...</p>
        </div>
    `;

    try {
        const response = await fetch(`${API_BASE}/markets/${marketId}`);
        if (!response.ok) throw new Error('Failed to load market');

        currentMarket = await response.json();

        // Load user's position and order history for this market if logged in
        currentUserPosition = null;
        currentMarketOrders = [];
        if (TokenManager.isLoggedIn()) {
            try {
                const [posResponse, ordersResponse] = await Promise.all([
                    apiRequest('/portfolio/positions'),
                    apiRequest(`/orders?market_id=${marketId}&limit=10`)
                ]);

                if (posResponse.ok) {
                    const positions = await posResponse.json();
                    currentUserPosition = positions.find(p => p.market_id === marketId);
                }
                if (ordersResponse.ok) {
                    currentMarketOrders = await ordersResponse.json();
                }
            } catch (e) {
                console.error('Could not load position/orders:', e);
            }
        }

        renderMarketDetail();
    } catch (error) {
        detail.innerHTML = `<p class="empty-state">Failed to load market details.</p>`;
    }
}

function renderMarketDetail() {
    if (!currentMarket) return;

    const market = currentMarket;
    const yesPercent = Math.round(market.yes_price * 100);
    const noPercent = Math.round(market.no_price * 100);
    const isLoggedIn = TokenManager.isLoggedIn();
    const isAdmin = TokenManager.getUser()?.is_admin || false;
    const hasPosition = currentUserPosition && (currentUserPosition.yes_shares > 0 || currentUserPosition.no_shares > 0);
    const hasOrders = currentMarketOrders.length > 0;

    document.getElementById('market-detail').innerHTML = `
        <div class="market-detail-header">
            <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                <span class="market-detail-category">${escapeHtml(market.category)}</span>
                ${isAdmin ? `<button class="btn btn-outline" style="color: var(--danger); border-color: var(--danger); font-size: 0.75rem; padding: 4px 12px;" onclick="deleteMarket(${market.id})">🗑️ Delete</button>` : ''}
            </div>
            <h2 class="market-detail-title">${escapeHtml(market.title)}</h2>
            ${market.description ? `<p class="market-detail-description">${escapeHtml(market.description)}</p>` : ''}
        </div>

        <div class="market-detail-prices">
            <div class="detail-price-box yes">
                <div class="detail-price-label">Yes</div>
                <div class="detail-price-value">${yesPercent} coins</div>
                <div class="detail-price-percent">${yesPercent}% chance</div>
            </div>
            <div class="detail-price-box no">
                <div class="detail-price-label">No</div>
                <div class="detail-price-value">${noPercent} coins</div>
                <div class="detail-price-percent">${noPercent}% chance</div>
            </div>
        </div>

        ${market.status === 'open' ? `
            ${hasPosition ? `
                <div class="position-section" style="background: var(--bg-glass); border: 2px solid var(--accent-primary); border-radius: var(--radius-lg); padding: var(--space-lg); margin-bottom: var(--space-lg);">
                    <h4 style="margin-bottom: var(--space-md); color: var(--text-primary); font-weight: 600;">Your Position</h4>
                    <div style="display: flex; gap: var(--space-lg); flex-wrap: wrap;">
                        ${currentUserPosition.yes_shares > 0 ? `
                            <div style="flex: 1; min-width: 140px; background: var(--success-bg); padding: var(--space-md); border-radius: var(--radius-md);">
                                <div style="font-size: 0.875rem; color: var(--text-muted);">Yes Shares</div>
                                <div style="font-size: 1.5rem; font-weight: 700; color: var(--yes-color);">${currentUserPosition.yes_shares}</div>
                                <button type="button" class="btn btn-sm" style="margin-top: var(--space-sm); background: var(--no-color); width: 100%;" 
                                    onclick="event.preventDefault(); event.stopPropagation(); sellPosition('yes', ${currentUserPosition.yes_shares})">
                                    Sell All Yes
                                </button>
                            </div>
                        ` : ''}
                        ${currentUserPosition.no_shares > 0 ? `
                            <div style="flex: 1; min-width: 140px; background: var(--danger-bg); padding: var(--space-md); border-radius: var(--radius-md);">
                                <div style="font-size: 0.875rem; color: var(--text-muted);">No Shares</div>
                                <div style="font-size: 1.5rem; font-weight: 700; color: var(--no-color);">${currentUserPosition.no_shares}</div>
                                <button type="button" class="btn btn-sm" style="margin-top: var(--space-sm); background: var(--no-color); width: 100%;" 
                                    onclick="event.preventDefault(); event.stopPropagation(); sellPosition('no', ${currentUserPosition.no_shares})">
                                    Sell All No
                                </button>
                            </div>
                        ` : ''}
                    </div>
                </div>
            ` : ''}
            
            <div class="trading-form">
                <h3 class="trading-form-title">Trade</h3>
                ${isLoggedIn ? `
                    <div class="trading-tabs">
                        <button class="trading-tab yes active" onclick="setTradingSide('yes')" id="tab-yes">Buy Yes</button>
                        <button class="trading-tab no" onclick="setTradingSide('no')" id="tab-no">Buy No</button>
                    </div>
                    <div class="quantity-input">
                        <label>Shares:</label>
                        <input type="number" id="trade-quantity" value="10" min="1" max="10000" onchange="updateTradeSummary()">
                    </div>
                    <div class="trade-summary">
                        <span class="trade-summary-label">Total Cost:</span>
                        <span class="trade-summary-value" id="trade-cost">🪙${Math.round(10 * market.yes_price * 100)}</span>
                    </div>
                    <div class="trading-buttons">
                        <button class="btn btn-yes" onclick="placeTrade('buy')" id="btn-trade">Buy Yes Shares</button>
                    </div>
                    
                    ${hasOrders ? `
                        <div class="orders-section" style="margin-top: var(--space-lg); padding-top: var(--space-lg); border-top: 1px solid var(--glass-border);">
                            <h4 style="margin-bottom: var(--space-md); color: var(--text-secondary);">Your Recent Orders</h4>
                            <div style="max-height: 200px; overflow-y: auto;">
                                ${currentMarketOrders.map(order => `
                                    <div style="display: flex; justify-content: space-between; padding: var(--space-sm) 0; border-bottom: 1px solid var(--glass-border-light); font-size: 0.875rem;">
                                        <span style="color: ${order.order_type === 'buy' ? 'var(--yes-color)' : 'var(--no-color)'}; font-weight: 500;">
                                            ${escapeHtml(order.order_type.toUpperCase())} ${order.quantity} ${escapeHtml(order.side.toUpperCase())}
                                        </span>
                                        <span style="color: var(--text-muted);">$${order.total_cost.toFixed(2)}</span>
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                    ` : ''}
                ` : `
                    <p style="color: var(--text-muted); text-align: center; padding: var(--space-lg);">
                        <a href="#" onclick="closeMarketModal(); showAuthModal('login'); return false;" style="color: var(--accent-primary);">Login</a> to start trading
                    </p>
                `}
            </div>
        ` : `
            <div class="trading-form" style="text-align: center;">
                <p style="color: ${market.resolved_outcome === 'yes' ? 'var(--yes-color)' : 'var(--no-color)'}; font-weight: 600;">
                    Resolved: ${escapeHtml(market.resolved_outcome?.toUpperCase() || 'UNKNOWN')}
                </p>
            </div>
        `}
    `;
}

function closeMarketModal() {
    document.getElementById('market-modal').classList.remove('show');
    currentMarket = null;
    currentUserPosition = null;
    currentMarketOrders = [];
}

// Category filter
document.addEventListener('DOMContentLoaded', () => {
    const filterBtns = document.querySelectorAll('.filter-btn');

    filterBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            filterBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            currentFilter = btn.dataset.category;
            renderMarkets();
        });
    });
});

// Helper functions
function formatNumber(num) {
    if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
    if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
    return num.toFixed(2);
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Create Market Modal functions
function showCreateMarketModal() {
    if (!TokenManager.isLoggedIn()) {
        showAuthModal('login');
        return;
    }
    document.getElementById('create-market-modal').classList.add('show');
    document.getElementById('create-market-form').reset();
    document.getElementById('create-market-error').textContent = '';

    // Set minimum date to tomorrow
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    document.getElementById('market-resolution-date').min = tomorrow.toISOString().split('T')[0];
}

function closeCreateMarketModal() {
    document.getElementById('create-market-modal').classList.remove('show');
}

async function handleCreateMarket(event) {
    event.preventDefault();

    const errorEl = document.getElementById('create-market-error');
    const submitBtn = document.getElementById('create-market-submit');

    const title = document.getElementById('market-title').value.trim();
    const description = document.getElementById('market-description').value.trim();
    const category = document.getElementById('market-category').value;
    const resolutionDate = document.getElementById('market-resolution-date').value;

    if (!title || !category || !resolutionDate) {
        errorEl.textContent = 'Please fill in all required fields';
        return;
    }

    if (title.length < 10) {
        errorEl.textContent = 'Question must be at least 10 characters';
        return;
    }

    errorEl.textContent = '';
    submitBtn.disabled = true;
    submitBtn.textContent = 'Submitting...';

    try {
        // Submit as proposal for admin review
        const response = await apiRequest('/proposals', {
            method: 'POST',
            body: JSON.stringify({
                title: title,
                description: description || null,
                category: category,
                resolution_date: resolutionDate + 'T23:59:59'
            })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to submit proposal');
        }

        closeCreateMarketModal();
        showToast('✅ Market proposal submitted! Awaiting admin approval.', 'success');

    } catch (error) {
        errorEl.textContent = error.message;
    } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = 'Submit Proposal';
    }
}

// Update UI to show create market button when logged in
function updateCreateMarketButton() {
    const btn = document.getElementById('create-market-btn');
    if (btn) {
        btn.style.display = TokenManager.isLoggedIn() ? 'block' : 'none';
    }
}

// Delete market (admin only)
async function deleteMarket(marketId) {
    if (!confirm('Are you sure you want to delete this market? This will also delete all orders and positions.')) {
        return;
    }

    try {
        const response = await apiRequest(`/markets/${marketId}`, {
            method: 'DELETE'
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to delete market');
        }

        const result = await response.json();
        closeMarketModal();
        showToast(result.message, 'success');
        await loadMarkets();

    } catch (error) {
        showToast('Error: ' + error.message, 'error');
    }
}

// Call on page load and auth state changes
document.addEventListener('DOMContentLoaded', () => {
    updateCreateMarketButton();
});
