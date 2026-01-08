/**
 * Trading Module
 * Handles order placement and portfolio management
 */

let tradingSide = 'yes';

function setTradingSide(side) {
    tradingSide = side;

    // Update tabs
    document.getElementById('tab-yes').classList.toggle('active', side === 'yes');
    document.getElementById('tab-no').classList.toggle('active', side === 'no');

    // Update button
    const btn = document.getElementById('btn-trade');
    if (side === 'yes') {
        btn.className = 'btn btn-yes';
        btn.textContent = 'Buy Yes Shares';
    } else {
        btn.className = 'btn btn-no';
        btn.textContent = 'Buy No Shares';
    }

    updateTradeSummary();
}

function updateTradeSummary() {
    if (!currentMarket) return;

    const quantity = parseInt(document.getElementById('trade-quantity').value) || 0;
    const price = tradingSide === 'yes' ? currentMarket.yes_price : currentMarket.no_price;
    const cost = quantity * price * 100; // Convert to coins
    document.getElementById('trade-cost').textContent = `🪙${Math.round(cost)}`;
}

async function placeTrade(orderType) {
    if (!TokenManager.isLoggedIn()) {
        showToast('Please login to trade', 'error');
        return;
    }

    if (!currentMarket) return;

    const quantity = parseInt(document.getElementById('trade-quantity').value);

    // Validate quantity
    if (isNaN(quantity) || quantity < 1) {
        showToast('Please enter a valid quantity (minimum 1)', 'error');
        return;
    }

    if (quantity > 10000) {
        showToast('Maximum order size is 10,000 shares', 'error');
        return;
    }

    const btn = document.getElementById('btn-trade');
    const originalText = btn.textContent;
    btn.disabled = true;
    btn.textContent = 'Processing...';

    try {
        const response = await apiRequest('/orders', {
            method: 'POST',
            body: JSON.stringify({
                market_id: currentMarket.id,
                side: tradingSide,
                order_type: orderType,
                quantity: quantity
            })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Order failed');
        }

        const order = await response.json();

        showToast(`Order filled: ${order.quantity} ${tradingSide.toUpperCase()} shares for 🪙${Math.round(order.total_cost * 100)}`, 'success');

        // Refresh data
        await refreshUserData();
        await loadMarkets();

        // Refresh market detail
        if (currentMarket) {
            await openMarketDetail(currentMarket.id);
        }

    } catch (error) {
        showToast(error.message, 'error');
    } finally {
        btn.disabled = false;
        btn.textContent = originalText;
    }
}

// Sell position function
async function sellPosition(side, quantity) {
    if (!TokenManager.isLoggedIn() || !currentMarket) return;

    const confirmSell = confirm(`Sell ${quantity} ${side.toUpperCase()} shares at current price?`);
    if (!confirmSell) return;

    try {
        const response = await apiRequest('/orders', {
            method: 'POST',
            body: JSON.stringify({
                market_id: currentMarket.id,
                side: side,
                order_type: 'sell',
                quantity: quantity
            })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Sell failed');
        }

        const order = await response.json();

        showToast(`Sold ${quantity} ${side.toUpperCase()} shares for 🪙${Math.round(order.total_cost * 100)}`, 'success');

        // Refresh data
        await refreshUserData();
        await loadMarkets();

        // Refresh market detail
        if (currentMarket) {
            await openMarketDetail(currentMarket.id);
        }

    } catch (error) {
        showToast(error.message, 'error');
    }
}

// Portfolio functions
async function loadPortfolio() {
    if (!TokenManager.isLoggedIn()) {
        document.getElementById('portfolio').style.display = 'none';
        return;
    }

    document.getElementById('portfolio').style.display = 'block';

    try {
        // Load portfolio summary
        const summaryResponse = await apiRequest('/portfolio/summary');
        if (summaryResponse.ok) {
            const summary = await summaryResponse.json();

            document.getElementById('portfolio-balance').textContent = `🪙${summary.balance.toLocaleString()}`;
            document.getElementById('portfolio-invested').textContent = `🪙${Math.round(summary.total_invested).toLocaleString()}`;
            document.getElementById('portfolio-value').textContent = `🪙${Math.round(summary.current_value).toLocaleString()}`;

            const pnlEl = document.getElementById('portfolio-pnl');
            const pnlCoins = Math.round(summary.profit_loss);
            const pnlText = `${pnlCoins >= 0 ? '+' : ''}🪙${pnlCoins.toLocaleString()}`;
            const pnlPct = summary.profit_loss_pct ? ` (${summary.profit_loss_pct >= 0 ? '+' : ''}${summary.profit_loss_pct.toFixed(1)}%)` : '';
            pnlEl.textContent = pnlText + pnlPct;
            pnlEl.style.color = summary.profit_loss >= 0 ? 'var(--yes-color)' : 'var(--no-color)';
        }

        // Load positions
        const positionsResponse = await apiRequest('/portfolio/positions');
        if (positionsResponse.ok) {
            const positions = await positionsResponse.json();
            renderPositions(positions);
        }

    } catch (error) {
        console.error('Error loading portfolio:', error);
    }
}

function renderPositions(positions) {
    const grid = document.getElementById('positions-grid');

    // Filter out empty positions
    const activePositions = positions.filter(p => p.yes_shares > 0 || p.no_shares > 0);

    if (activePositions.length === 0) {
        grid.innerHTML = `<p class="empty-state">No positions yet. Start trading!</p>`;
        return;
    }

    grid.innerHTML = activePositions.map(pos => `
        <div class="position-card">
            <h4 class="position-title">${escapeHtml(pos.market_title || `Market #${pos.market_id}`)}</h4>
            <div class="position-shares">
                ${pos.yes_shares > 0 ? `
                    <div class="share-info">
                        <span class="share-label">Yes Shares</span>
                        <span class="share-value yes">${pos.yes_shares} @ ${Math.round(pos.avg_yes_price * 100)} coins</span>
                    </div>
                ` : ''}
                ${pos.no_shares > 0 ? `
                    <div class="share-info">
                        <span class="share-label">No Shares</span>
                        <span class="share-value no">${pos.no_shares} @ ${(pos.avg_no_price * 100).toFixed(0)}¢</span>
                    </div>
                ` : ''}
            </div>
            <div style="display: flex; gap: var(--space-md); margin-top: var(--space-md);">
                <span style="color: var(--text-muted); font-size: 0.875rem;">
                    Current: Yes ${(pos.current_yes_price * 100).toFixed(0)}¢ / No ${(pos.current_no_price * 100).toFixed(0)}¢
                </span>
            </div>
        </div>
    `).join('');
}

// Navigate to portfolio
document.addEventListener('DOMContentLoaded', () => {
    const portfolioLinks = document.querySelectorAll('a[href="#portfolio"]');

    portfolioLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            if (TokenManager.isLoggedIn()) {
                loadPortfolio();
                document.getElementById('portfolio').scrollIntoView({ behavior: 'smooth' });
            } else {
                showAuthModal('login');
            }
        });
    });
});
