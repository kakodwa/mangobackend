/* ============================================
   API CLIENT
   ============================================ */

class APIClient {
  constructor(baseUrl = CONFIG.API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  getAuthHeader() {
    const token = localStorage.getItem(CONFIG.TOKEN_KEY);
    return token ? { Authorization: `Bearer ${token}` } : {};
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseUrl}${endpoint}`;
    const headers = {
      'Content-Type': 'application/json',
      ...this.getAuthHeader(),
      ...options.headers
    };

    try {
      const response = await fetch(url, {
        ...options,
        headers
      });

      if (response.status === 401) {
        localStorage.removeItem(CONFIG.TOKEN_KEY);
        localStorage.removeItem(CONFIG.USER_KEY);
        window.location.href = 'dashboard.html';
        return null;
      }

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.message || `HTTP error! status: ${response.status}`);
      }

      return data;
    } catch (error) {
      console.error('[v0] API Error:', error);
      throw error;
    }
  }

  // Admin Authentication
  async login(email, password) {
    return this.request('admin/login/', {
      method: 'POST',
      body: JSON.stringify({ email, password })
    });
  }

  async logout() {
    return this.request('admin/logout/', { method: 'POST' });
  }

  // Dashboard Stats
  async getDashboardStats() {
    return this.request('admin/dashboard/stats/');
  }

  // Posts Management
  async getPendingPosts(page = 1, pageSize = 10) {
    return this.request(`admin/posts/pending/?page=${page}&page_size=${pageSize}`);
  }

  async getAllPosts(page = 1, pageSize = 10) {
    return this.request(`admin/posts/?page=${page}&page_size=${pageSize}`);
  }

  async getPostDetail(postId) {
    return this.request(`admin/posts/${postId}/`);
  }

  async approvePost(postId) {
    return this.request(`admin/posts/${postId}/approve/`, { method: 'POST' });
  }

  async rejectPost(postId, reason = '') {
    return this.request(`admin/posts/${postId}/reject/`, {
      method: 'POST',
      body: JSON.stringify({ reason })
    });
  }

  async updatePost(postId, data) {
    return this.request(`admin/posts/${postId}/`, {
      method: 'PUT',
      body: JSON.stringify(data)
    });
  }

  // User Management
  async getUsers(page = 1, pageSize = 10) {
    return this.request(`admin/users/?page=${page}&page_size=${pageSize}`);
  }

  async getUserDetail(userId) {
    return this.request(`admin/users/${userId}/`);
  }

  async suspendUser(userId) {
    return this.request(`admin/users/${userId}/suspend/`, { method: 'POST' });
  }

  async activateUser(userId) {
    return this.request(`admin/users/${userId}/activate/`, { method: 'POST' });
  }

  async deleteUser(userId) {
    return this.request(`admin/users/${userId}/`, { method: 'DELETE' });
  }

  // Wallet & Transactions
  async getWalletBalance() {
    return this.request('admin/wallet/balance/');
  }

  async getTransactions(page = 1, pageSize = 10, filters = {}) {
    const query = new URLSearchParams({ page, page_size: pageSize, ...filters }).toString();
    return this.request(`admin/transactions/?${query}`);
  }

  async getPendingWithdrawals() {
    return this.request('admin/withdrawals/pending/');
  }

  async approveWithdrawal(withdrawalId) {
    return this.request(`admin/withdrawals/${withdrawalId}/approve/`, { method: 'POST' });
  }

  async rejectWithdrawal(withdrawalId, reason = '') {
    return this.request(`admin/withdrawals/${withdrawalId}/reject/`, {
      method: 'POST',
      body: JSON.stringify({ reason })
    });
  }

  async exportTransactions(format = 'csv') {
    return this.request(`admin/transactions/export/?format=${format}`);
  }

  // Commission Settings
  async getCommissionRates() {
    return this.request('admin/commission-rates/');
  }

  async updateCommissionRates(rates) {
    return this.request('admin/commission-rates/', {
      method: 'PUT',
      body: JSON.stringify(rates)
    });
  }

  // Admin Settings
  async updateAdminProfile(data) {
    return this.request('admin/profile/', {
      method: 'PUT',
      body: JSON.stringify(data)
    });
  }

  async changePassword(currentPassword, newPassword) {
    return this.request('admin/change-password/', {
      method: 'POST',
      body: JSON.stringify({ current_password: currentPassword, new_password: newPassword })
    });
  }

  async updateAppSettings(settings) {
    return this.request('admin/settings/', {
      method: 'PUT',
      body: JSON.stringify(settings)
    });
  }
}

// Create global API client instance
const apiClient = new APIClient();

console.log('[v0] API Client initialized');
