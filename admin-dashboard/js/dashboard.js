/* ============================================
   DASHBOARD FUNCTIONALITY
   ============================================ */

// State Management
let dashboardState = {
  posts: [],
  users: [],
  transactions: [],
  withdrawals: [],
  stats: {},
  paginators: {
    posts: new Paginator([], 10),
    users: new Paginator([], 10),
    transactions: new Paginator([], 10)
  }
};

let selectedPost = null;

// ============================================
// Initialization
// ============================================

function initializeDashboard() {
  // Load initial data
  loadDashboardData();
  
  // Setup navigation
  setupNavigation();
  
  // Setup tab switching
  setupTabs();
  
  // Refresh data periodically
  setInterval(loadDashboardData, 60000); // Every minute
}

function setupNavigation() {
  const navLinks = document.querySelectorAll('.nav-link[data-section]');
  navLinks.forEach(link => {
    link.addEventListener('click', function(e) {
      e.preventDefault();
      const section = this.dataset.section;
      showSection(section);
      
      // Update active state
      navLinks.forEach(l => l.classList.remove('active'));
      this.classList.add('active');
    });
  });
}

function setupTabs() {
  window.switchTab = function(tabName, button) {
    const tabMap = {
      'transactions': 'transactionsTab',
      'withdrawals': 'withdrawalsTab',
      'commission': 'commissionTab'
    };
    
    const tabId = tabMap[tabName];
    if (!tabId) return;
    
    // Hide all tabs
    document.querySelectorAll('.tab-content').forEach(tab => {
      tab.classList.remove('active');
    });
    
    // Show selected tab
    const selectedTab = document.getElementById(tabId);
    if (selectedTab) {
      selectedTab.classList.add('active');
    }
    
    // Update active button
    document.querySelectorAll('.tab').forEach(tab => {
      tab.classList.remove('active');
    });
    if (button) {
      button.classList.add('active');
    }
  };
}

function showSection(section) {
  const sectionMap = {
    'overview': 'overviewSection',
    'posts': 'postsSection',
    'users': 'usersSection',
    'wallet': 'walletSection',
    'settings': 'settingsSection'
  };
  
  const sectionId = sectionMap[section];
  if (!sectionId) return;
  
  // Hide all sections
  document.querySelectorAll('.section').forEach(sec => {
    sec.classList.remove('active');
  });
  
  // Show selected section
  const selectedSection = document.getElementById(sectionId);
  if (selectedSection) {
    selectedSection.classList.add('active');
    
    // Update header title
    const titles = {
      'overview': 'Dashboard Overview',
      'posts': 'Post Approval & Moderation',
      'users': 'User Management',
      'wallet': 'Wallet & Transactions',
      'settings': 'Settings'
    };
    document.getElementById('sectionTitle').textContent = titles[section] || 'Dashboard';
    
    // Load section-specific data
    if (section === 'posts') loadPosts();
    else if (section === 'users') loadUsers();
    else if (section === 'wallet') loadWalletData();
  }
}

// ============================================
// Data Loading Functions
// ============================================

async function loadDashboardData() {
  console.log('[v0] Loading dashboard data...');
  
  try {
    // Load overview stats
    const stats = {
      totalUsers: 1240,
      pendingPosts: 15,
      totalTransactions: 5342,
      companyBalance: 12450.75,
      monthlyRevenue: 3200.50
    };
    
    dashboardState.stats = stats;
    updateOverviewStats(stats);
    
    // Load mock data for demo
    dashboardState.posts = generateMockPosts(25);
    dashboardState.users = generateMockUsers(30);
    dashboardState.transactions = generateMockTransactions(50);
    dashboardState.withdrawals = generateMockWithdrawals(8);
    
    // Initialize paginators
    dashboardState.paginators.posts.setData(dashboardState.posts);
    dashboardState.paginators.users.setData(dashboardState.users);
    dashboardState.paginators.transactions.setData(dashboardState.transactions);
    
    console.log('[v0] Dashboard data loaded successfully');
  } catch (error) {
    console.error('[v0] Error loading dashboard data:', error);
    showToast('Failed to load dashboard data', 'error');
  }
}

function updateOverviewStats(stats) {
  document.getElementById('totalUsers').textContent = stats.totalUsers.toLocaleString();
  document.getElementById('pendingPosts').textContent = stats.pendingPosts;
  document.getElementById('totalTransactions').textContent = stats.totalTransactions.toLocaleString();
  document.getElementById('companyBalance').textContent = formatCurrency(stats.companyBalance);
  
  // Update recent activity
  updateRecentActivity();
}

function updateRecentActivity() {
  const recentActivityList = document.getElementById('recentActivityList');
  const activities = [
    { icon: '✓', text: 'Post approved by admin', time: '2 minutes ago' },
    { icon: '💳', text: 'Transaction completed', time: '15 minutes ago' },
    { icon: '👤', text: 'New user registered', time: '1 hour ago' },
    { icon: '⏳', text: '3 posts pending review', time: '2 hours ago' },
    { icon: '💰', text: 'Withdrawal request received', time: '3 hours ago' }
  ];
  
  recentActivityList.innerHTML = activities.map(activity => `
    <div style="padding: var(--spacing-md); border-bottom: 1px solid var(--border); display: flex; align-items: center; gap: var(--spacing-md);">
      <span style="font-size: 18px; width: 24px; text-align: center;">${activity.icon}</span>
      <div style="flex: 1;">
        <div style="font-size: 14px;">${activity.text}</div>
        <div style="font-size: 12px; color: var(--text-secondary);">${activity.time}</div>
      </div>
    </div>
  `).join('');
}

async function loadPosts() {
  console.log('[v0] Loading posts...');
  const paginator = dashboardState.paginators.posts;
  renderPostsTable(paginator.getPageData());
  updatePostsPageInfo(paginator);
}

async function loadUsers() {
  console.log('[v0] Loading users...');
  const paginator = dashboardState.paginators.users;
  renderUsersTable(paginator.getPageData());
  updateUsersPageInfo(paginator);
}

async function loadTransactions() {
  console.log('[v0] Loading transactions...');
  const paginator = dashboardState.paginators.transactions;
  renderTransactionsTable(paginator.getPageData());
  updateTransactionsPageInfo(paginator);
}

async function loadWalletData() {
  console.log('[v0] Loading wallet data...');
  
  const stats = dashboardState.stats;
  document.getElementById('walletBalance').textContent = formatCurrency(stats.companyBalance || 0);
  document.getElementById('monthlyRevenue').textContent = formatCurrency(stats.monthlyRevenue || 0);
  document.getElementById('walletTotalTx').textContent = dashboardState.transactions.length;
  document.getElementById('pendingWithdrawals').textContent = dashboardState.withdrawals.length;
  
  // Load transactions and withdrawals
  loadTransactions();
  renderWithdrawalsTable(dashboardState.withdrawals);
}

async function refreshPosts() {
  showToast('Refreshing posts...', 'info');
  await loadDashboardData();
  loadPosts();
}

async function refreshUsers() {
  showToast('Refreshing users...', 'info');
  await loadDashboardData();
  loadUsers();
}

async function refreshTransactions() {
  showToast('Refreshing transactions...', 'info');
  loadTransactions();
}

// ============================================
// Posts Table Functions
// ============================================

function renderPostsTable(posts) {
  const tbody = document.getElementById('postsTable');
  
  if (posts.length === 0) {
    tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; padding: var(--spacing-lg);"><div class="empty-state"><p>No posts to display</p></div></td></tr>';
    return;
  }
  
  tbody.innerHTML = posts.map(post => `
    <tr>
      <td>#${post.id}</td>
      <td>${post.author}</td>
      <td>${truncateText(post.title, 30)}</td>
      <td>${post.category}</td>
      <td>${formatDate(post.date)}</td>
      <td>${buildStatusBadge(post.status)}</td>
      <td>${buildActionButtons([
        { icon: '👁️', label: 'View', variant: 'text', onclick: `viewPost(${post.id})` },
        { icon: post.status === 'pending' ? '✓' : '', label: post.status === 'pending' ? 'Approve' : '', variant: 'success', onclick: `approvePost(${post.id})` },
        { icon: post.status === 'pending' ? '✕' : '', label: post.status === 'pending' ? 'Reject' : '', variant: 'danger', onclick: `rejectPost(${post.id})` }
      ].filter(btn => btn.label))}</td>
    </tr>
  `).join('');
}

function filterPosts() {
  const search = document.getElementById('postSearch').value;
  const status = document.getElementById('statusFilter').value;
  
  let filtered = dashboardState.posts;
  
  if (search) {
    filtered = searchArray(filtered, search, ['title', 'author', 'category']);
  }
  
  if (status) {
    filtered = filterArray(filtered, { status });
  }
  
  dashboardState.paginators.posts.setData(filtered);
  loadPosts();
}

function updatePostsPageInfo(paginator) {
  document.getElementById('postsPageInfo').textContent = paginator.getPageInfo();
}

function nextPostsPage() {
  if (dashboardState.paginators.posts.nextPage()) {
    loadPosts();
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }
}

function previousPostsPage() {
  if (dashboardState.paginators.posts.previousPage()) {
    loadPosts();
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }
}

function changePostsPageSize() {
  const size = document.querySelector('select[onchange="changePostsPageSize()"]').value;
  dashboardState.paginators.posts.setPageSize(size);
  loadPosts();
}

function viewPost(postId) {
  const post = dashboardState.posts.find(p => p.id === postId);
  if (!post) return;
  
  selectedPost = post;
  const content = document.getElementById('postDetailContent');
  content.innerHTML = `
    <div class="detail-section">
      <h4>Post Information</h4>
      <div class="detail-row">
        <span class="detail-label">ID</span>
        <span class="detail-value">#${post.id}</span>
      </div>
      <div class="detail-row">
        <span class="detail-label">Title</span>
        <span class="detail-value">${post.title}</span>
      </div>
      <div class="detail-row">
        <span class="detail-label">Author</span>
        <span class="detail-value">${post.author}</span>
      </div>
      <div class="detail-row">
        <span class="detail-label">Category</span>
        <span class="detail-value">${post.category}</span>
      </div>
      <div class="detail-row">
        <span class="detail-label">Date Posted</span>
        <span class="detail-value">${formatDate(post.date)}</span>
      </div>
      <div class="detail-row">
        <span class="detail-label">Status</span>
        <span class="detail-value">${buildStatusBadge(post.status)}</span>
      </div>
      <div class="detail-row">
        <span class="detail-label">Description</span>
        <span class="detail-value">${post.description}</span>
      </div>
    </div>
  `;
  
  // Show/hide action buttons based on status
  document.getElementById('approvePostBtn').style.display = post.status === 'pending' ? 'block' : 'none';
  document.getElementById('rejectPostBtn').style.display = post.status === 'pending' ? 'block' : 'none';
  
  openModal('postDetailModal');
}

async function approvePost(postId = null) {
  const id = postId || selectedPost.id;
  try {
    // Simulate API call
    const post = dashboardState.posts.find(p => p.id === id);
    if (post) {
      post.status = 'approved';
      showToast(`Post #${id} approved successfully`, 'success');
      closeModal('postDetailModal');
      loadPosts();
    }
  } catch (error) {
    showToast('Failed to approve post', 'error');
  }
}

async function rejectPost(postId = null) {
  const id = postId || selectedPost.id;
  try {
    // Simulate API call
    const post = dashboardState.posts.find(p => p.id === id);
    if (post) {
      post.status = 'rejected';
      showToast(`Post #${id} rejected`, 'success');
      closeModal('postDetailModal');
      loadPosts();
    }
  } catch (error) {
    showToast('Failed to reject post', 'error');
  }
}

// ============================================
// Users Table Functions
// ============================================

function renderUsersTable(users) {
  const tbody = document.getElementById('usersTable');
  
  if (users.length === 0) {
    tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; padding: var(--spacing-lg);"><div class="empty-state"><p>No users to display</p></div></td></tr>';
    return;
  }
  
  tbody.innerHTML = users.map(user => `
    <tr>
      <td>#${user.id}</td>
      <td>${user.name}</td>
      <td>${user.email}</td>
      <td>${user.phone}</td>
      <td>${buildStatusBadge(user.status)}</td>
      <td>${formatCurrency(user.balance)}</td>
      <td>${buildActionButtons([
        { icon: '👁️', label: 'View', variant: 'text', onclick: `viewUser(${user.id})` },
        { icon: user.status === 'active' ? '⏸' : '▶️', label: user.status === 'active' ? 'Suspend' : 'Activate', variant: 'outline', onclick: `toggleUserStatus(${user.id})` }
      ])}</td>
    </tr>
  `).join('');
}

function filterUsers() {
  const search = document.getElementById('userSearch').value;
  const status = document.getElementById('userStatusFilter').value;
  
  let filtered = dashboardState.users;
  
  if (search) {
    filtered = searchArray(filtered, search, ['name', 'email', 'phone']);
  }
  
  if (status) {
    filtered = filterArray(filtered, { status });
  }
  
  dashboardState.paginators.users.setData(filtered);
  loadUsers();
}

function updateUsersPageInfo(paginator) {
  document.getElementById('usersPageInfo').textContent = paginator.getPageInfo();
}

function nextUsersPage() {
  if (dashboardState.paginators.users.nextPage()) {
    loadUsers();
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }
}

function previousUsersPage() {
  if (dashboardState.paginators.users.previousPage()) {
    loadUsers();
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }
}

function changeUsersPageSize() {
  const size = document.querySelector('select[onchange="changeUsersPageSize()"]').value;
  dashboardState.paginators.users.setPageSize(size);
  loadUsers();
}

function viewUser(userId) {
  const user = dashboardState.users.find(u => u.id === userId);
  if (!user) return;
  
  alert(`User Profile: ${user.name}\nEmail: ${user.email}\nBalance: ${formatCurrency(user.balance)}`);
}

function toggleUserStatus(userId) {
  const user = dashboardState.users.find(u => u.id === userId);
  if (user) {
    user.status = user.status === 'active' ? 'inactive' : 'active';
    showToast(`User ${user.status}`, 'success');
    loadUsers();
  }
}

// ============================================
// Transactions Table Functions
// ============================================

function renderTransactionsTable(transactions) {
  const tbody = document.getElementById('transactionsTable');
  
  if (transactions.length === 0) {
    tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; padding: var(--spacing-lg);"><div class="empty-state"><p>No transactions to display</p></div></td></tr>';
    return;
  }
  
  tbody.innerHTML = transactions.map(tx => `
    <tr>
      <td>${tx.id}</td>
      <td>${formatDate(tx.date)}</td>
      <td>${tx.user}</td>
      <td>${formatCurrency(tx.amount)}</td>
      <td>${tx.type.charAt(0).toUpperCase() + tx.type.slice(1)}</td>
      <td>${buildStatusBadge(tx.status)}</td>
    </tr>
  `).join('');
}

function filterTransactions() {
  const search = document.getElementById('txSearch').value;
  const type = document.getElementById('txTypeFilter').value;
  
  let filtered = dashboardState.transactions;
  
  if (search) {
    filtered = searchArray(filtered, search, ['id', 'user']);
  }
  
  if (type) {
    filtered = filterArray(filtered, { type });
  }
  
  dashboardState.paginators.transactions.setData(filtered);
  loadTransactions();
}

function updateTransactionsPageInfo(paginator) {
  document.getElementById('txPageInfo').textContent = paginator.getPageInfo();
}

function nextTxPage() {
  if (dashboardState.paginators.transactions.nextPage()) {
    loadTransactions();
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }
}

function previousTxPage() {
  if (dashboardState.paginators.transactions.previousPage()) {
    loadTransactions();
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }
}

function changeTxPageSize() {
  const size = document.querySelector('select[onchange="changeTxPageSize()"]').value;
  dashboardState.paginators.transactions.setPageSize(size);
  loadTransactions();
}

function exportTransactions() {
  const columns = [
    { key: 'id', label: 'ID' },
    { key: 'date', label: 'Date' },
    { key: 'user', label: 'User' },
    { key: 'amount', label: 'Amount' },
    { key: 'type', label: 'Type' },
    { key: 'status', label: 'Status' }
  ];
  
  exportToCSV(dashboardState.transactions, 'transactions.csv', columns);
  showToast('Transactions exported successfully', 'success');
}

// ============================================
// Withdrawals Table Functions
// ============================================

function renderWithdrawalsTable(withdrawals) {
  const tbody = document.getElementById('withdrawalsTable');
  
  if (withdrawals.length === 0) {
    tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; padding: var(--spacing-lg);"><div class="empty-state"><p>No pending withdrawals</p></div></td></tr>';
    return;
  }
  
  tbody.innerHTML = withdrawals.map(wd => `
    <tr>
      <td>${wd.id}</td>
      <td>${wd.user}</td>
      <td>${formatCurrency(wd.amount)}</td>
      <td>${formatDate(wd.requested)}</td>
      <td>${buildStatusBadge(wd.status)}</td>
      <td>${buildActionButtons([
        { icon: '✓', label: 'Approve', variant: 'success', onclick: `approveWithdrawal(${wd.id})` },
        { icon: '✕', label: 'Reject', variant: 'danger', onclick: `rejectWithdrawal(${wd.id})` }
      ])}</td>
    </tr>
  `).join('');
}

function approveWithdrawal(withdrawalId) {
  const wd = dashboardState.withdrawals.find(w => w.id === `WD${String(withdrawalId).padStart(5, '0')}`);
  if (wd) {
    dashboardState.withdrawals = dashboardState.withdrawals.filter(w => w.id !== wd.id);
    showToast(`Withdrawal approved: ${wd.id}`, 'success');
    renderWithdrawalsTable(dashboardState.withdrawals);
    loadWalletData();
  }
}

function rejectWithdrawal(withdrawalId) {
  const wd = dashboardState.withdrawals.find(w => parseInt(w.id.slice(2)) === withdrawalId);
  if (wd) {
    dashboardState.withdrawals = dashboardState.withdrawals.filter(w => w.id !== wd.id);
    showToast(`Withdrawal rejected: ${wd.id}`, 'success');
    renderWithdrawalsTable(dashboardState.withdrawals);
    loadWalletData();
  }
}

// ============================================
// Commission Settings Functions
// ============================================

function saveCommissionRates() {
  const rates = {
    product_sales: parseFloat(document.getElementById('newProductRate').value) || parseFloat(document.getElementById('productRate').value),
    service: parseFloat(document.getElementById('newServiceRate').value) || parseFloat(document.getElementById('serviceRate').value),
    subscription: parseFloat(document.getElementById('newSubscriptionRate').value) || parseFloat(document.getElementById('subscriptionRate').value)
  };
  
  // Update display values
  document.getElementById('productRate').value = rates.product_sales;
  document.getElementById('serviceRate').value = rates.service;
  document.getElementById('subscriptionRate').value = rates.subscription;
  
  // Clear input fields
  document.getElementById('newProductRate').value = '';
  document.getElementById('newServiceRate').value = '';
  document.getElementById('newSubscriptionRate').value = '';
  
  showToast('Commission rates updated successfully', 'success');
}

function resetCommissionRates() {
  document.getElementById('newProductRate').value = '';
  document.getElementById('newServiceRate').value = '';
  document.getElementById('newSubscriptionRate').value = '';
  showToast('Form reset', 'info');
}

// ============================================
// Settings Functions
// ============================================

function saveProfileSettings() {
  const name = document.getElementById('settingsName').value;
  const email = document.getElementById('settingsEmail').value;
  
  if (!name || !email) {
    showToast('Please fill in all fields', 'error');
    return;
  }
  
  const user = getStoredUser();
  user.name = name;
  user.email = email;
  setSession(getStoredToken(), user);
  
  showToast('Profile updated successfully', 'success');
  updateUserUI();
}

function changePassword() {
  const current = document.getElementById('currentPassword').value;
  const newPwd = document.getElementById('newPassword').value;
  const confirm = document.getElementById('confirmPassword').value;
  
  if (!current || !newPwd || !confirm) {
    showToast('Please fill in all password fields', 'error');
    return;
  }
  
  if (newPwd !== confirm) {
    showToast('Passwords do not match', 'error');
    return;
  }
  
  if (newPwd.length < 6) {
    showToast('Password must be at least 6 characters', 'error');
    return;
  }
  
  // Clear fields
  document.getElementById('currentPassword').value = '';
  document.getElementById('newPassword').value = '';
  document.getElementById('confirmPassword').value = '';
  
  showToast('Password changed successfully', 'success');
}

function saveAppSettings() {
  const appName = document.getElementById('appName').value;
  const commission = document.getElementById('defaultCommission').value;
  
  if (!appName || !commission) {
    showToast('Please fill in all fields', 'error');
    return;
  }
  
  showToast('App settings updated successfully', 'success');
}

// Initialize dashboard when page loads
document.addEventListener('DOMContentLoaded', function() {
  setTimeout(() => {
    if (isAuthenticated()) {
      initializeDashboard();
    }
  }, 100);
});

console.log('[v0] Dashboard module loaded');
