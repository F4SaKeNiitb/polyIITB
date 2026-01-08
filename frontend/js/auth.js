/**
 * Authentication Module
 * Handles JWT token management and auth UI
 */

const API_BASE = '/api';

// Token management
const TokenManager = {
    getAccessToken() {
        return localStorage.getItem('access_token');
    },

    getRefreshToken() {
        return localStorage.getItem('refresh_token');
    },

    setTokens(accessToken, refreshToken) {
        localStorage.setItem('access_token', accessToken);
        localStorage.setItem('refresh_token', refreshToken);
    },

    clearTokens() {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user');
    },

    getUser() {
        const user = localStorage.getItem('user');
        return user ? JSON.parse(user) : null;
    },

    setUser(user) {
        localStorage.setItem('user', JSON.stringify(user));
    },

    isLoggedIn() {
        return !!this.getAccessToken();
    }
};

// API helper with auth
async function apiRequest(endpoint, options = {}, skipRefresh = false) {
    const token = TokenManager.getAccessToken();

    const headers = {
        'Content-Type': 'application/json',
        ...options.headers
    };

    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(`${API_BASE}${endpoint}`, {
        ...options,
        headers
    });

    // Only try refresh if not explicitly skipped and we have a refresh token
    if (response.status === 401 && !skipRefresh && TokenManager.getRefreshToken()) {
        // Try to refresh token
        const refreshed = await refreshAccessToken();
        if (refreshed) {
            headers['Authorization'] = `Bearer ${TokenManager.getAccessToken()}`;
            return fetch(`${API_BASE}${endpoint}`, { ...options, headers });
        } else {
            // Don't call logout here - just return the failed response
            // Let the calling code decide what to do
            console.warn('Token refresh failed');
        }
    }

    return response;
}

async function refreshAccessToken() {
    try {
        const refreshToken = TokenManager.getRefreshToken();
        if (!refreshToken) return false;

        const response = await fetch(`${API_BASE}/auth/refresh`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ refresh_token: refreshToken })
        });

        if (response.ok) {
            const data = await response.json();
            TokenManager.setTokens(data.access_token, data.refresh_token);
            return true;
        }
    } catch (error) {
        console.error('Token refresh failed:', error);
    }
    return false;
}

// Auth Modal Management
let currentAuthMode = 'login';

function showAuthModal(mode = 'login') {
    currentAuthMode = mode;
    updateAuthModalUI();
    document.getElementById('auth-modal').classList.add('show');
    document.getElementById('auth-error').textContent = '';
    document.getElementById('auth-form').reset();
}

function closeAuthModal() {
    document.getElementById('auth-modal').classList.remove('show');
}

function toggleAuthMode() {
    currentAuthMode = currentAuthMode === 'login' ? 'register' : 'login';
    updateAuthModalUI();
    document.getElementById('auth-error').textContent = '';
}

function updateAuthModalUI() {
    const isLogin = currentAuthMode === 'login';

    document.getElementById('auth-title').textContent = isLogin ? 'Login' : 'Create Account';
    document.getElementById('auth-subtitle').textContent = isLogin
        ? 'Welcome back to PolyIITB'
        : 'Start trading predictions today';
    document.getElementById('username-group').style.display = isLogin ? 'none' : 'block';
    document.getElementById('auth-submit').textContent = isLogin ? 'Login' : 'Create Account';
    document.getElementById('auth-switch-text').textContent = isLogin
        ? "Don't have an account?"
        : 'Already have an account?';
    document.getElementById('auth-switch-link').textContent = isLogin ? 'Sign up' : 'Login';
}

async function handleAuth(event) {
    event.preventDefault();

    const errorEl = document.getElementById('auth-error');
    const submitBtn = document.getElementById('auth-submit');
    const email = document.getElementById('auth-email').value;
    const password = document.getElementById('auth-password').value;

    errorEl.textContent = '';
    submitBtn.disabled = true;
    submitBtn.textContent = currentAuthMode === 'login' ? 'Logging in...' : 'Creating account...';

    try {
        // Clear old tokens before login to avoid conflicts
        TokenManager.clearTokens();

        if (currentAuthMode === 'register') {
            const username = document.getElementById('auth-username').value;

            if (!username || username.length < 3) {
                throw new Error('Username must be at least 3 characters');
            }

            // Register
            const registerResponse = await fetch(`${API_BASE}/auth/register`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, password, username })
            });

            if (!registerResponse.ok) {
                const error = await registerResponse.json();
                throw new Error(error.detail || 'Registration failed');
            }
        }

        // Login
        const formData = new URLSearchParams();
        formData.append('username', email);  // OAuth2 uses 'username' field
        formData.append('password', password);

        const loginResponse = await fetch(`${API_BASE}/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: formData
        });

        if (!loginResponse.ok) {
            const error = await loginResponse.json();
            throw new Error(error.detail || 'Login failed');
        }

        const tokens = await loginResponse.json();
        TokenManager.setTokens(tokens.access_token, tokens.refresh_token);

        // Get user info - use direct fetch with new token, skip refresh logic
        const userResponse = await fetch(`${API_BASE}/auth/me`, {
            headers: {
                'Authorization': `Bearer ${tokens.access_token}`,
                'Content-Type': 'application/json'
            }
        });

        if (userResponse.ok) {
            const user = await userResponse.json();
            TokenManager.setUser(user);
        } else {
            // Even if getting user fails, we're logged in with tokens
            console.warn('Could not fetch user info, but login succeeded');
        }

        closeAuthModal();
        updateUIForAuthState();
        showToast('Welcome to PolyIITB!', 'success');

        // Refresh data
        loadMarkets();

    } catch (error) {
        errorEl.textContent = error.message;
    } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = currentAuthMode === 'login' ? 'Login' : 'Create Account';
    }
}

function logout() {
    TokenManager.clearTokens();
    updateUIForAuthState();
    showToast('Logged out successfully', 'success');

    // Hide portfolio if visible
    document.getElementById('portfolio').style.display = 'none';
    document.getElementById('markets').scrollIntoView({ behavior: 'smooth' });
}

function updateUIForAuthState() {
    const isLoggedIn = TokenManager.isLoggedIn();
    const user = TokenManager.getUser();

    document.getElementById('nav-auth').style.display = isLoggedIn ? 'none' : 'flex';
    document.getElementById('nav-user').style.display = isLoggedIn ? 'flex' : 'none';
    document.getElementById('nav-portfolio').style.display = isLoggedIn ? 'block' : 'none';

    if (isLoggedIn && user) {
        document.getElementById('user-balance').textContent = `🪙 ${user.balance.toLocaleString()}`;
        document.getElementById('user-name').textContent = user.username;
        document.getElementById('user-avatar').textContent = user.username.charAt(0).toUpperCase();
    }

    // Update create market button visibility
    if (typeof updateCreateMarketButton === 'function') {
        updateCreateMarketButton();
    }

    // Show admin link only for admin users
    const adminLink = document.getElementById('admin-link');
    if (adminLink && user) {
        adminLink.style.display = user.is_admin ? 'block' : 'none';
    }
}

async function refreshUserData() {
    if (!TokenManager.isLoggedIn()) return;

    try {
        const response = await apiRequest('/auth/me', {}, true);  // Skip refresh on failure
        if (response.ok) {
            const user = await response.json();
            TokenManager.setUser(user);
            updateUIForAuthState();
        }
    } catch (error) {
        console.error('Failed to refresh user data:', error);
    }
}

// User dropdown
document.addEventListener('DOMContentLoaded', () => {
    const userBtn = document.getElementById('user-btn');
    const dropdownMenu = document.getElementById('dropdown-menu');

    if (userBtn) {
        userBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            dropdownMenu.classList.toggle('show');
        });
    }

    document.addEventListener('click', () => {
        dropdownMenu?.classList.remove('show');
    });
});
