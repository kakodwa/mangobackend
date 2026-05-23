/* ============================================
   AUTHENTICATION MODULE
   ============================================ */

// ============================================
// Session Management
// ============================================

function isAuthenticated() {
  return !!localStorage.getItem(CONFIG.TOKEN_KEY);
}

function getStoredUser() {
  const user = localStorage.getItem(CONFIG.USER_KEY);
  return user ? JSON.parse(user) : null;
}

function getStoredToken() {
  return localStorage.getItem(CONFIG.TOKEN_KEY);
}

function setSession(token, user) {
  localStorage.setItem(CONFIG.TOKEN_KEY, token);
  localStorage.setItem(CONFIG.USER_KEY, JSON.stringify(user));
}

function clearSession() {
  localStorage.removeItem(CONFIG.TOKEN_KEY);
  localStorage.removeItem(CONFIG.USER_KEY);
}

// ============================================
// Login/Logout Functions
// ============================================

async function handleLogin(email, password, rememberMe = false) {
  try {
    // For demo purposes, validate against demo credentials
    if (email === CONFIG.DEMO_EMAIL && password === CONFIG.DEMO_PASSWORD) {
      const demoToken = 'demo_token_' + Date.now();
      const demoUser = {
        id: 1,
        email: email,
        name: 'Admin User',
        role: 'admin'
      };
      
      setSession(demoToken, demoUser);
      return { success: true, user: demoUser };
    }
    
    // In production, make actual API call
    // const response = await apiClient.login(email, password);
    // setSession(response.token, response.user);
    // return { success: true, user: response.user };
    
    // For demo, show error
    throw new Error('Invalid credentials. Use admin@mango.com / password123');
  } catch (error) {
    console.error('[v0] Login error:', error);
    return { success: false, error: error.message };
  }
}

function logout() {
  clearSession();
  window.location.href = 'dashboard.html';
}

// ============================================
// UI Authentication Functions
// ============================================

function toggleAuthUI() {
  const isAuth = isAuthenticated();
  const loginModal = document.getElementById('loginModal');
  const dashboardLayout = document.getElementById('dashboardLayout');
  
  if (isAuth) {
    if (loginModal) loginModal.classList.add('hidden');
    if (dashboardLayout) dashboardLayout.style.display = 'flex';
    updateUserUI();
  } else {
    if (loginModal) loginModal.classList.remove('hidden');
    if (dashboardLayout) dashboardLayout.style.display = 'none';
  }
}

function updateUserUI() {
  const user = getStoredUser();
  if (!user) return;
  
  // Update avatar initial
  const avatar = document.getElementById('adminAvatar');
  if (avatar) {
    avatar.textContent = user.name.charAt(0).toUpperCase();
  }
  
  // Update user info
  const nameEl = document.getElementById('adminName');
  const emailEl = document.getElementById('adminEmail');
  if (nameEl) nameEl.textContent = user.name || 'Admin User';
  if (emailEl) emailEl.textContent = user.email || 'admin@example.com';
  
  // Update settings form
  const settingsName = document.getElementById('settingsName');
  const settingsEmail = document.getElementById('settingsEmail');
  if (settingsName) settingsName.value = user.name || '';
  if (settingsEmail) settingsEmail.value = user.email || '';
}

// ============================================
// Form Handlers
// ============================================

function initAuthForms() {
  // Landing page login form
  const landingLoginForm = document.getElementById('loginForm');
  if (landingLoginForm) {
    landingLoginForm.addEventListener('submit', async function(e) {
      e.preventDefault();
      const email = document.getElementById('email').value;
      const password = document.getElementById('password').value;
      const remember = document.getElementById('loginForm').querySelector('input[name="remember"]').checked;
      
      const result = await handleLogin(email, password, remember);
      if (result.success) {
        window.location.href = 'dashboard.html';
      } else {
        document.getElementById('loginError').textContent = result.error;
        showToast(result.error, 'error');
      }
    });
  }
  
  // Dashboard login form
  const dashboardLoginForm = document.getElementById('dashboardLoginForm');
  if (dashboardLoginForm) {
    dashboardLoginForm.addEventListener('submit', async function(e) {
      e.preventDefault();
      const email = document.getElementById('loginEmail').value;
      const password = document.getElementById('loginPassword').value;
      const remember = document.getElementById('rememberMe').checked;
      
      const result = await handleLogin(email, password, remember);
      if (result.success) {
        closeModal('loginModal');
        toggleAuthUI();
        initializeDashboard();
        showToast('Login successful!', 'success');
      } else {
        document.getElementById('dashLoginError').textContent = result.error;
        showToast(result.error, 'error');
      }
    });
  }
}

// ============================================
// Protected Route Check
// ============================================

function checkAuthentication() {
  // Only check on dashboard page
  if (window.location.pathname.includes('dashboard.html') || window.location.pathname === '/dashboard') {
    const isAuth = isAuthenticated();
    const loginModal = document.getElementById('loginModal');
    const dashboardLayout = document.getElementById('dashboardLayout');
    
    // Make sure forms are initialized first
    setTimeout(() => {
      initAuthForms();
      toggleAuthUI();
    }, 100);
  } else if (window.location.pathname.includes('index.html') || window.location.pathname === '/') {
    // On landing page, initialize login form
    setTimeout(() => {
      initAuthForms();
    }, 100);
  }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
  checkAuthentication();
  updateTime();
});

console.log('[v0] Authentication module loaded');
