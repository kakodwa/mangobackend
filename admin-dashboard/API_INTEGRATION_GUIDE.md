# API Integration Guide - Mango Marketplace Admin Dashboard

This guide explains how to integrate the Mango Admin Dashboard with the Django REST Framework backend to display real data from your marketplaces.

## Quick Overview

The Mango Marketplace has 4 main marketplace APIs:

1. **E-Commerce** - Products, shops, orders
2. **Real Estate** - Properties and listings  
3. **Hospitality** - Lodges, rooms, bookings
4. **Events** - Events and tickets

## Backend Structure

Based on your Django project structure, the API endpoints are:

```
Base URL: http://localhost:8000/api/

Admin Endpoints:
- GET    /api/products/           - List all products
- GET    /api/products/{id}/      - Get product details
- GET    /api/properties/         - List all properties
- GET    /api/properties/{id}/    - Get property details
- GET    /api/lodges/             - List all lodges
- GET    /api/rooms/              - List all rooms
- GET    /api/events/             - List all events
- GET    /api/tickets/            - List all tickets
- GET    /api/orders/             - List all orders
- GET    /api/bookings/           - List all bookings
- GET    /api/transactions/       - List all transactions
```

## Frontend Files to Update

The API client is already set up in `js/api-client.js`. Here's how to use it:

### 1. Update API Base URL

**File:** `js/api-client.js`

Find this line:
```javascript
const API_BASE_URL = 'http://localhost:8000/api/';
```

This should point to your Django backend. If your backend is running on a different port or domain, update it accordingly.

### 2. Update Dashboard Data Loading

**File:** `js/dashboard.js`

Look for the `initDashboard()` function. The dashboard currently uses mock data. To use real API data:

#### Example 1: Load Products (E-Commerce)

Replace this:
```javascript
// Current mock data
const mockPosts = generateMockPosts(25);
```

With this:
```javascript
// Fetch real data from API
async function loadECommerceData() {
  try {
    const response = await fetch(`${API_BASE_URL}products/`, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      }
    });
    const products = await response.json();
    displayProducts(products);
  } catch (error) {
    console.error('Error loading products:', error);
    showToast('Failed to load products', 'error');
  }
}
```

#### Example 2: Load Properties (Real Estate)

```javascript
async function loadPropertyData() {
  try {
    const response = await fetch(`${API_BASE_URL}properties/`, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      }
    });
    const properties = await response.json();
    displayProperties(properties);
  } catch (error) {
    console.error('Error loading properties:', error);
    showToast('Failed to load properties', 'error');
  }
}
```

#### Example 3: Load Lodges (Hospitality)

```javascript
async function loadHospitalityData() {
  try {
    const response = await fetch(`${API_BASE_URL}lodges/`, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      }
    });
    const lodges = await response.json();
    displayLodges(lodges);
  } catch (error) {
    console.error('Error loading lodges:', error);
    showToast('Failed to load lodges', 'error');
  }
}
```

#### Example 4: Load Events (Events & Ticketing)

```javascript
async function loadEventData() {
  try {
    const response = await fetch(`${API_BASE_URL}events/`, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      }
    });
    const events = await response.json();
    displayEvents(events);
  } catch (error) {
    console.error('Error loading events:', error);
    showToast('Failed to load events', 'error');
  }
}
```

## Authentication

The dashboard uses JWT token-based authentication. The token is stored in `localStorage` after admin login:

```javascript
// Token is automatically stored during login in auth.js
const token = localStorage.getItem('token');

// Use it in API requests
const headers = {
  'Authorization': `Bearer ${token}`,
  'Content-Type': 'application/json'
};
```

## Current Mock Data (Demo Mode)

The dashboard comes with mock data generators for testing without a backend:

- **mockPosts** - 25 sample posts with approval queue
- **mockUsers** - 30 sample users 
- **mockTransactions** - 50 sample transactions
- **mockWithdrawals** - 8 sample withdrawal requests

These are in `js/main.js` in the `generateMock*` functions.

## How to Implement Full API Integration

### Step 1: Backend Requirements

Your Django backend must:

1. **Enable CORS** - Allow requests from your frontend
   ```python
   # settings.py
   CORS_ALLOWED_ORIGINS = [
       "http://localhost:8080",
       "http://localhost:3000",
       "https://yourdomain.com",
   ]
   ```

2. **Provide Authentication Endpoint**
   ```
   POST /api/auth/login/
   Body: {"email": "admin@example.com", "password": "password"}
   Response: {"token": "jwt_token_here"}
   ```

3. **Provide Data Endpoints** (examples below)

### Step 2: Update Auth Login

**File:** `js/auth.js`

Update the login function to call your backend:

```javascript
async function handleLogin(email, password) {
  try {
    const response = await fetch(`${API_BASE_URL}auth/login/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });
    
    const data = await response.json();
    
    if (response.ok) {
      localStorage.setItem('token', data.token);
      localStorage.setItem('user', JSON.stringify(data.user));
      window.location.href = 'dashboard.html';
    } else {
      throw new Error(data.detail || 'Login failed');
    }
  } catch (error) {
    showToast(error.message, 'error');
  }
}
```

### Step 3: Replace Mock Data with API Calls

In `js/dashboard.js`, replace the mock data initialization with API calls:

```javascript
async function initDashboard() {
  // Load real data from backend
  await Promise.all([
    loadDashboardStats(),
    loadPostsForApproval(),
    loadUsers(),
    loadTransactions(),
    loadWithdrawals()
  ]);
  
  setupEventListeners();
}

async function loadDashboardStats() {
  try {
    const response = await fetch(`${API_BASE_URL}dashboard/stats/`, {
      headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
    });
    const stats = await response.json();
    updateStatsCards(stats);
  } catch (error) {
    console.error('Error loading stats:', error);
  }
}

async function loadPostsForApproval() {
  try {
    const response = await fetch(`${API_BASE_URL}posts/?status=pending`, {
      headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
    });
    const posts = await response.json();
    displayPostQueue(posts);
  } catch (error) {
    console.error('Error loading posts:', error);
  }
}
```

## API Response Formats

### Products/Posts Response
```json
{
  "count": 25,
  "results": [
    {
      "id": 1,
      "title": "Product Name",
      "description": "Product description",
      "status": "pending",
      "created_at": "2024-01-15T10:30:00Z",
      "seller": {
        "id": 1,
        "name": "Seller Name",
        "email": "seller@example.com"
      }
    }
  ]
}
```

### Properties Response
```json
{
  "count": 10,
  "results": [
    {
      "id": 1,
      "title": "Property Name",
      "description": "Property details",
      "price": 500000,
      "location": "City, Country",
      "amenities": ["WiFi", "Parking", "Pool"],
      "images": ["url1", "url2"],
      "owner": {
        "id": 1,
        "name": "Owner Name"
      }
    }
  ]
}
```

### Lodges/Rooms Response
```json
{
  "count": 15,
  "results": [
    {
      "id": 1,
      "name": "Lodge Name",
      "description": "Lodge description",
      "rooms": 5,
      "room_list": [
        {
          "id": 1,
          "name": "Standard Room",
          "price_per_night": 5000,
          "available": true
        }
      ],
      "location": "City, Country"
    }
  ]
}
```

### Events Response
```json
{
  "count": 20,
  "results": [
    {
      "id": 1,
      "title": "Event Name",
      "description": "Event details",
      "date": "2024-02-15T18:00:00Z",
      "location": "Venue, City",
      "tickets_available": 100,
      "price_per_ticket": 2000,
      "organizer": {
        "id": 1,
        "name": "Organizer Name"
      }
    }
  ]
}
```

### Transactions Response
```json
{
  "count": 50,
  "results": [
    {
      "id": 1,
      "user": {
        "id": 1,
        "name": "User Name",
        "email": "user@example.com"
      },
      "type": "purchase",
      "amount": 50000,
      "status": "completed",
      "created_at": "2024-01-15T10:30:00Z",
      "description": "Purchase of Product"
    }
  ]
}
```

## Dashboard Features Ready for API Integration

The following dashboard features are ready to work with API endpoints:

### 1. Overview Stats
- Total Users
- Total Products
- Total Transactions
- Total Revenue

### 2. Posts Approval Queue
- List pending posts/products
- Approve/Reject posts
- View post details
- Search and filter

### 3. User Management
- List all users
- Suspend/Activate users
- View user details
- Search and filter

### 4. Wallet & Transactions
- View company wallet balance
- Transaction history with CSV export
- Filter by transaction type
- Pagination support

### 5. Pending Withdrawals
- View pending withdrawal requests
- Approve/Reject withdrawals
- Update admin wallet on approval

### 6. Commission Settings
- Adjust commission rates for different transaction types
- Save settings to backend

## Testing Without Backend

The dashboard includes a **Demo Mode** where it generates mock data automatically. This is perfect for testing the UI and functionality before your API is ready.

To use demo mode, just:
1. Login with email: `admin@mango.com` and password: `password123`
2. The dashboard will automatically load mock data
3. All features will work with simulated data

## Next Steps

1. **Set up CORS** on your Django backend
2. **Create authentication endpoint** at `/api/auth/login/`
3. **Create API endpoints** for each marketplace data
4. **Test API calls** using Postman or curl
5. **Update frontend** to call your API endpoints
6. **Deploy** to production

## Troubleshooting

### "Failed to connect to API"
- Check if Django backend is running
- Verify API_BASE_URL in js/api-client.js
- Check CORS settings in Django

### "Authentication failed"
- Verify token format (should be JWT)
- Check token expiration time
- Verify Authorization header format

### "CORS error"
- Add your frontend domain to CORS_ALLOWED_ORIGINS in Django settings
- Ensure CORS middleware is installed
- Test with curl or Postman first

## Support

For issues or questions about API integration:
1. Check the Django project README
2. Review the API endpoint structure
3. Use browser DevTools Network tab to debug requests
4. Check Django server logs for errors

---

**Ready to connect your backend?** Follow the steps above and update the API endpoints in `js/api-client.js` and `js/dashboard.js`!
