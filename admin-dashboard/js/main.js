/* ============================================
   MAIN UTILITY FUNCTIONS
   ============================================ */

// Configuration
const CONFIG = {
  API_BASE_URL: 'http://localhost:8000/api/',
  TOKEN_KEY: 'admin_token',
  USER_KEY: 'admin_user',
  DEMO_EMAIL: 'admin@mango.com',
  DEMO_PASSWORD: 'password123'
};

// ============================================
// Toast Notifications
// ============================================

function showToast(message, type = 'info', duration = 3000) {
  const toastContainer = document.getElementById('toastContainer');
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  
  const icon = {
    success: '✓',
    error: '✕',
    warning: '⚠',
    info: 'ℹ'
  }[type] || 'ℹ';
  
  toast.innerHTML = `<span>${icon}</span><span>${message}</span>`;
  toastContainer.appendChild(toast);
  
  setTimeout(() => {
    toast.style.animation = 'slideOut 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, duration);
}

// ============================================
// Modal Functions
// ============================================

function openModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) {
    modal.classList.remove('hidden');
  }
}

function closeModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) {
    modal.classList.add('hidden');
  }
}

// Close modal when clicking overlay
document.addEventListener('DOMContentLoaded', function() {
  const modals = document.querySelectorAll('.modal-overlay');
  modals.forEach(modal => {
    modal.addEventListener('click', function(e) {
      if (e.target === this) {
        this.classList.add('hidden');
      }
    });
  });
});

// ============================================
// Formatting Functions
// ============================================

function formatCurrency(amount) {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD'
  }).format(amount);
}

function formatDate(dateString) {
  const options = { year: 'numeric', month: 'short', day: 'numeric' };
  return new Date(dateString).toLocaleDateString('en-US', options);
}

function formatDateTime(dateString) {
  const options = { 
    year: 'numeric', 
    month: 'short', 
    day: 'numeric', 
    hour: '2-digit', 
    minute: '2-digit'
  };
  return new Date(dateString).toLocaleDateString('en-US', options);
}

function truncateText(text, maxLength = 50) {
  return text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
}

// ============================================
// Table Building Functions
// ============================================

function buildTableRow(data, columns) {
  const row = document.createElement('tr');
  columns.forEach(col => {
    const td = document.createElement('td');
    const value = data[col.key];
    
    if (col.render) {
      td.innerHTML = col.render(value, data);
    } else if (col.type === 'currency') {
      td.textContent = formatCurrency(value);
    } else if (col.type === 'date') {
      td.textContent = formatDate(value);
    } else {
      td.textContent = value || '-';
    }
    
    row.appendChild(td);
  });
  return row;
}

function buildStatusBadge(status) {
  const statusMap = {
    'pending': { class: 'status-pending', text: 'Pending' },
    'approved': { class: 'status-approved', text: 'Approved' },
    'rejected': { class: 'status-rejected', text: 'Rejected' },
    'active': { class: 'status-active', text: 'Active' },
    'inactive': { class: 'status-inactive', text: 'Inactive' },
    'completed': { class: 'status-approved', text: 'Completed' },
    'failed': { class: 'status-rejected', text: 'Failed' }
  };
  
  const info = statusMap[status] || { class: 'status-pending', text: status };
  return `<span class="status-badge ${info.class}">${info.text}</span>`;
}

function buildActionButtons(actions) {
  let html = '<div class="table-actions">';
  
  actions.forEach(action => {
    const classes = `btn btn-${action.variant || 'outline'} btn-small action-btn`;
    html += `<button class="${classes}" onclick="${action.onclick}" title="${action.label}">${action.icon || action.label}</button>`;
  });
  
  html += '</div>';
  return html;
}

// ============================================
// Pagination Functions
// ============================================

class Paginator {
  constructor(data = [], pageSize = 10) {
    this.data = data;
    this.pageSize = pageSize;
    this.currentPage = 1;
  }
  
  setData(data) {
    this.data = data;
    this.currentPage = 1;
  }
  
  setPageSize(size) {
    this.pageSize = parseInt(size);
    this.currentPage = 1;
  }
  
  getCurrentPage() {
    return this.currentPage;
  }
  
  getPageSize() {
    return this.pageSize;
  }
  
  getTotalPages() {
    return Math.ceil(this.data.length / this.pageSize);
  }
  
  getTotalItems() {
    return this.data.length;
  }
  
  getPageData() {
    const start = (this.currentPage - 1) * this.pageSize;
    const end = start + this.pageSize;
    return this.data.slice(start, end);
  }
  
  nextPage() {
    if (this.currentPage < this.getTotalPages()) {
      this.currentPage++;
      return true;
    }
    return false;
  }
  
  previousPage() {
    if (this.currentPage > 1) {
      this.currentPage--;
      return true;
    }
    return false;
  }
  
  goToPage(page) {
    const pageNum = parseInt(page);
    if (pageNum >= 1 && pageNum <= this.getTotalPages()) {
      this.currentPage = pageNum;
      return true;
    }
    return false;
  }
  
  getPageInfo() {
    const start = (this.currentPage - 1) * this.pageSize + 1;
    const end = Math.min(this.currentPage * this.pageSize, this.data.length);
    return `${start}-${end} of ${this.data.length}`;
  }
}

// ============================================
// Search & Filter Functions
// ============================================

function searchArray(array, query, searchFields) {
  if (!query.trim()) return array;
  
  const lowerQuery = query.toLowerCase();
  return array.filter(item => {
    return searchFields.some(field => {
      const value = item[field];
      return value && value.toString().toLowerCase().includes(lowerQuery);
    });
  });
}

function filterArray(array, filters) {
  return array.filter(item => {
    return Object.keys(filters).every(key => {
      if (!filters[key]) return true;
      return item[key] === filters[key];
    });
  });
}

// ============================================
// Form Validation
// ============================================

function validateEmail(email) {
  const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return regex.test(email);
}

function validatePassword(password) {
  return password && password.length >= 6;
}

function validateRequired(value) {
  return value && value.toString().trim().length > 0;
}

// ============================================
// Time Display
// ============================================

function updateTime() {
  const timeElement = document.getElementById('headerTime');
  if (timeElement) {
    const now = new Date();
    const options = { hour: '2-digit', minute: '2-digit', second: '2-digit' };
    const timeString = now.toLocaleTimeString('en-US', options);
    timeElement.textContent = timeString;
  }
}

setInterval(updateTime, 1000);

// ============================================
// Generate Mock Data (for demo purposes)
// ============================================

function generateMockPosts(count = 25) {
  const titles = [
    'Beautiful Vintage Sofa',
    'Brand New iPhone 14',
    'Handmade Ceramic Vase',
    'Professional Camera Setup',
    'Organic Coffee Beans',
    'Fitness Equipment Set',
    'Vintage Leather Jacket',
    'Smart Home Hub Device'
  ];
  
  const categories = ['Electronics', 'Furniture', 'Fashion', 'Home & Garden', 'Sports', 'Arts & Crafts'];
  const statuses = ['pending', 'approved', 'rejected'];
  const authors = ['john_doe', 'jane_smith', 'mike_wilson', 'sarah_jones', 'alex_brown'];
  
  const posts = [];
  for (let i = 1; i <= count; i++) {
    posts.push({
      id: i,
      title: titles[Math.floor(Math.random() * titles.length)],
      author: authors[Math.floor(Math.random() * authors.length)],
      category: categories[Math.floor(Math.random() * categories.length)],
      status: statuses[Math.floor(Math.random() * statuses.length)],
      date: new Date(Date.now() - Math.random() * 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
      description: 'Lorem ipsum dolor sit amet, consectetur adipiscing elit.'
    });
  }
  return posts;
}

function generateMockUsers(count = 30) {
  const firstNames = ['John', 'Jane', 'Mike', 'Sarah', 'Alex', 'Emma', 'David', 'Lisa'];
  const lastNames = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis'];
  const domains = ['gmail.com', 'yahoo.com', 'hotmail.com', 'company.com'];
  const statuses = ['active', 'inactive'];
  
  const users = [];
  for (let i = 1; i <= count; i++) {
    const firstName = firstNames[Math.floor(Math.random() * firstNames.length)];
    const lastName = lastNames[Math.floor(Math.random() * lastNames.length)];
    users.push({
      id: i,
      name: `${firstName} ${lastName}`,
      email: `${firstName.toLowerCase()}.${lastName.toLowerCase()}@${domains[Math.floor(Math.random() * domains.length)]}`,
      phone: `+1 ${Math.random().toString().slice(2, 5)}-${Math.random().toString().slice(2, 5)}-${Math.random().toString().slice(2, 6)}`,
      status: statuses[Math.floor(Math.random() * statuses.length)],
      balance: (Math.random() * 1000).toFixed(2),
      joined: new Date(Date.now() - Math.random() * 365 * 24 * 60 * 60 * 1000).toISOString().split('T')[0]
    });
  }
  return users;
}

function generateMockTransactions(count = 50) {
  const users = generateMockUsers(5).map(u => u.name);
  const types = ['payment', 'commission', 'withdrawal', 'refund'];
  const statuses = ['completed', 'pending', 'failed'];
  
  const transactions = [];
  for (let i = 1; i <= count; i++) {
    transactions.push({
      id: `TXN${String(i).padStart(6, '0')}`,
      date: new Date(Date.now() - Math.random() * 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
      user: users[Math.floor(Math.random() * users.length)],
      amount: (Math.random() * 500 + 10).toFixed(2),
      type: types[Math.floor(Math.random() * types.length)],
      status: statuses[Math.floor(Math.random() * statuses.length)]
    });
  }
  return transactions;
}

function generateMockWithdrawals(count = 8) {
  const users = generateMockUsers(5).map(u => ({ name: u.name, id: u.id }));
  const statuses = ['pending'];
  
  const withdrawals = [];
  for (let i = 1; i <= count; i++) {
    const user = users[Math.floor(Math.random() * users.length)];
    withdrawals.push({
      id: `WD${String(i).padStart(5, '0')}`,
      user: user.name,
      userId: user.id,
      amount: (Math.random() * 500 + 100).toFixed(2),
      requested: new Date(Date.now() - Math.random() * 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
      status: 'pending'
    });
  }
  return withdrawals;
}

// ============================================
// CSV Export Function
// ============================================

function exportToCSV(data, filename, columns) {
  const headers = columns.map(col => col.label);
  const rows = data.map(item => {
    return columns.map(col => {
      const value = item[col.key];
      if (typeof value === 'string' && value.includes(',')) {
        return `"${value}"`;
      }
      return value || '';
    });
  });
  
  const csv = [headers, ...rows].map(row => row.join(',')).join('\n');
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
  const link = document.createElement('a');
  const url = URL.createObjectURL(blob);
  
  link.setAttribute('href', url);
  link.setAttribute('download', filename);
  link.style.visibility = 'hidden';
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}

// ============================================
// Chart Color Helpers
// ============================================

const CHART_COLORS = {
  primary: '#6200EE',
  secondary: '#03DAC6',
  success: '#4CAF50',
  danger: '#F44336',
  warning: '#FF9800',
  info: '#2196F3'
};

console.log('[v0] Main utilities loaded successfully');
