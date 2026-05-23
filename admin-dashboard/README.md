# Mango Marketplace Admin Dashboard

A professional, web-based admin dashboard for managing the Mango Marketplace. Built with vanilla HTML, CSS, and JavaScript with a focus on usability, responsiveness, and performance.

## Features

### 🎯 Core Functionality
- **Admin Authentication**: Secure login with session management
- **Dashboard Overview**: Real-time stats and recent activity
- **Post Management**: Approve/reject user-posted content with review queue
- **User Management**: View, suspend, and manage users
- **Wallet & Transactions**: Track company finances and approve withdrawals
- **Commission Settings**: Configure transaction fees and commissions
- **Admin Settings**: Profile, security, and app configuration

### 🎨 Design Features
- **Modern UI**: Clean, professional design with purple and teal color scheme
- **Responsive Layout**: Works perfectly on desktop, tablet, and mobile
- **Dark Navigation**: Intuitive sidebar navigation with active indicators
- **Data Tables**: Sortable, filterable tables with pagination
- **Modal Dialogs**: Detailed views and confirmation dialogs
- **Toast Notifications**: User-friendly feedback messages
- **Status Badges**: Visual status indicators for posts and users

## Project Structure

```
admin-dashboard/
├── css/
│   ├── styles.css              # Global styles and theme
│   ├── landing.css             # Landing page specific styles
│   └── dashboard.css           # Dashboard specific styles
├── js/
│   ├── main.js                 # Utility functions and helpers
│   ├── auth.js                 # Authentication logic
│   ├── api-client.js           # API communication
│   └── dashboard.js            # Dashboard functionality
├── index.html                  # Landing page
├── dashboard.html              # Admin dashboard
└── README.md                   # This file
```

## Getting Started

### Prerequisites
- Modern web browser (Chrome, Firefox, Safari, Edge)
- HTTP server (for CORS support)
- Backend API running (optional - demo mode works without backend)

### Installation

1. **Clone the repository**:
```bash
git clone <repository-url>
cd admin-dashboard
```

2. **Start a local server** (Python):
```bash
python -m http.server 8080
```

Or with Node.js:
```bash
npx http-server
```

3. **Open in browser**:
```
http://localhost:8080
```

### Demo Credentials
- **Email**: `admin@mango.com`
- **Password**: `password123`

## Usage Guide

### Landing Page (`index.html`)
The landing page showcases the app with:
- Hero section with app overview
- Feature highlights
- App screenshot placeholders (ready for real images)
- Download links for iOS/Android
- API documentation section
- Admin login form

### Admin Dashboard (`dashboard.html`)

#### Overview Section
- Total users count
- Pending posts for review
- Total transactions processed
- Company wallet balance
- Recent activity feed

#### Posts Management
- Queue of pending posts requiring approval
- Search and filter by title, author, or category
- View full post details
- Approve or reject posts
- Pagination support (10, 25, 50 items per page)

#### User Management
- View all registered users
- Search by name, email, or phone
- Suspend/activate user accounts
- View user balance and status
- Manage user permissions (extensible)

#### Wallet & Transactions
**Company Wallet**:
- Total balance display
- Monthly revenue summary
- Transaction count
- Pending withdrawals count

**Transactions Tab**:
- Full transaction history
- Filter by type and date range
- Export to CSV
- Real-time status updates

**Pending Withdrawals**:
- List of withdrawal requests
- Quick approve/reject actions
- User details and amounts

**Commission Settings**:
- Configure rates for different transaction types
- Product sales commission
- Service commission
- Subscription fees

#### Settings
- Admin profile management (name, email)
- Change password with validation
- App configuration settings

## Color Palette

The dashboard uses a carefully chosen color palette matching the Flutter frontend:

```css
--primary: #6200EE      /* Purple - Main actions */
--secondary: #03DAC6    /* Teal - Accents */
--success: #4CAF50      /* Green - Approvals */
--danger: #F44336       /* Red - Rejections */
--background: #FAFAFA   /* Off-white */
--surface: #FFFFFF      /* White */
--text-primary: #212121 /* Dark gray */
--text-secondary: #757575 /* Medium gray */
--border: #E0E0E0       /* Light gray */
```

## API Integration

The dashboard is designed to integrate with the Django backend. Key API endpoints:

### Authentication
- `POST /api/admin/login/` - Admin login
- `POST /api/admin/logout/` - Admin logout

### Dashboard
- `GET /api/admin/dashboard/stats/` - Dashboard statistics

### Posts Management
- `GET /api/admin/posts/pending/` - Get pending posts
- `POST /api/admin/posts/{id}/approve/` - Approve post
- `POST /api/admin/posts/{id}/reject/` - Reject post

### Users
- `GET /api/admin/users/` - Get user list
- `POST /api/admin/users/{id}/suspend/` - Suspend user
- `POST /api/admin/users/{id}/activate/` - Activate user

### Wallet & Transactions
- `GET /api/admin/wallet/balance/` - Get company balance
- `GET /api/admin/transactions/` - Get transactions
- `GET /api/admin/withdrawals/pending/` - Get pending withdrawals
- `POST /api/admin/withdrawals/{id}/approve/` - Approve withdrawal

### Commission
- `GET /api/admin/commission-rates/` - Get current rates
- `PUT /api/admin/commission-rates/` - Update rates

**Note**: The current implementation uses mock data for demonstration. To connect to the actual backend, update the API calls in `js/dashboard.js` to use the `apiClient` methods.

## Configuration

### API Base URL
Edit `js/main.js`:
```javascript
const CONFIG = {
  API_BASE_URL: 'http://localhost:8000/api/',
  // ... other config
};
```

### Demo Mode
The dashboard works in demo mode without a backend. It generates mock data for:
- Posts (25 items)
- Users (30 items)
- Transactions (50 items)
- Withdrawals (8 items)

## Browser Support

- Chrome/Edge 90+
- Firefox 88+
- Safari 14+
- Responsive design supports:
  - Desktop (1200px+)
  - Tablet (768px - 1199px)
  - Mobile (320px - 767px)

## Performance Features

- **Vanilla JavaScript**: No framework overhead
- **Efficient DOM Updates**: Minimal reflows and repaints
- **Pagination**: Handles large datasets efficiently
- **Search & Filter**: Client-side filtering with optimized algorithms
- **Local Storage**: Session caching for better performance
- **Lazy Loading**: Ready for image and asset optimization

## Security Considerations

### Current Implementation
- JWT token storage in localStorage (for demo)
- Token validation on API requests
- Protected route access

### Production Recommendations
- Implement secure HTTP-only cookies for tokens
- Add CSRF protection
- Implement rate limiting
- Add server-side session validation
- Encrypt sensitive data in transit and at rest
- Regular security audits

## Customization

### Adding New Features
1. Create new section in `dashboard.html`
2. Add navigation link in sidebar
3. Add CSS for styling in `css/dashboard.css`
4. Implement logic in `js/dashboard.js`
5. Connect API calls in `js/api-client.js`

### Styling
- Global styles: `css/styles.css`
- Colors: Update CSS variables in `:root`
- Spacing: Use `--spacing-*` variables
- Fonts: Already optimized with system fonts

### Mock Data
Update the mock data generators in `js/main.js`:
- `generateMockPosts()`
- `generateMockUsers()`
- `generateMockTransactions()`
- `generateMockWithdrawals()`

## Troubleshooting

### Login Issues
- Verify credentials: `admin@mango.com` / `password123`
- Check browser console for errors
- Clear localStorage and try again

### API Connection Issues
- Verify backend is running
- Check `API_BASE_URL` in `js/main.js`
- Enable CORS on backend
- Check network tab in DevTools

### Data Not Loading
- Verify mock data is generating (check console)
- Check for JavaScript errors in console
- Try refreshing the page
- Clear browser cache

## Development

### Local Development
1. Run HTTP server: `python -m http.server 8080`
2. Open browser: `http://localhost:8080`
3. Make changes to files
4. Browser auto-refresh (or manual refresh)

### Testing
- Test in multiple browsers
- Test responsive design (use DevTools)
- Test keyboard navigation
- Test with screen readers

## Deployment

### Static Hosting
The dashboard can be deployed to any static host:
- Vercel
- Netlify
- AWS S3
- GitHub Pages
- Any HTTP server

### Steps
1. Build/minify assets (optional)
2. Deploy all files to static host
3. Update `API_BASE_URL` for production
4. Set up SSL/TLS
5. Configure CORS on backend
6. Test in production environment

## License

Proprietary - Mango Marketplace

## Support

For issues, questions, or feature requests:
1. Check the troubleshooting section
2. Review the console for error messages
3. Contact the development team

## Changelog

### Version 1.0.0 (Initial Release)
- Landing page with features and downloads
- Admin dashboard with overview
- Post approval/moderation system
- User management
- Wallet and transaction tracking
- Commission rate settings
- Admin profile and security settings
- Responsive design for all devices
- Mock data for demo purposes

---

**Built with ❤️ for the Mango Marketplace Admin Team**
