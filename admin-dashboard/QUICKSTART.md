# Mango Admin Dashboard - Quick Start Guide

## 🚀 Get Started in 5 Minutes

### 1. Open the Application

**Option A: Using Python**
```bash
cd admin-dashboard
python -m http.server 8080
# Open http://localhost:8080 in your browser
```

**Option B: Using Node.js**
```bash
cd admin-dashboard
npx http-server
# Open http://localhost:8080 in your browser
```

**Option C: Direct File Opening**
- Simply open `index.html` in your browser (limited functionality without a server)

### 2. Explore the Landing Page

When you open the app, you'll see:
- **Hero Section**: App overview and key features
- **Features Grid**: 6 key marketplace features
- **App Screenshots**: Placeholder areas for app images
- **Download Section**: iOS/Android/Web app download buttons
- **API Documentation**: Links to API docs and resources
- **Admin Login Form**: At the bottom of the page

### 3. Login to Admin Dashboard

**Click "Admin Dashboard"** button or scroll to the login form.

**Demo Credentials**:
- Email: `admin@mango.com`
- Password: `password123`

After logging in, you'll see the admin dashboard interface.

## 📊 Dashboard Overview

### 1. **Overview Tab** (Default)
View key statistics:
- Total Users: 1,240
- Pending Posts: 15
- Total Transactions: 5,342
- Company Balance: $12,450.75
- Recent Activity Feed

### 2. **Posts Management**
Manage user-posted content:
- **View** pending posts awaiting approval
- **Approve** to make them live
- **Reject** inappropriate content
- **Search** posts by title, author, or category
- **Filter** by status (Pending, Approved, Rejected)
- **Pagination**: View 10, 25, or 50 items per page

**How to Approve a Post**:
1. Click the "👁️" icon in the Actions column to view details
2. Review the post information in the modal
3. Click "✓ Approve" to accept or "✕ Reject" to decline

### 3. **User Management**
Manage marketplace users:
- View all registered users
- See user details (name, email, phone, status)
- View account balance
- **Suspend** active users (disable their account)
- **Activate** suspended users (re-enable their account)

### 4. **Wallet & Transactions**

#### Company Wallet Summary
Shows at the top in a gradient card:
- Total Balance
- Monthly Revenue
- Total Transactions
- Pending Withdrawals

#### Three Tabs:

**A. Transactions**
- Complete transaction history
- Filter by type (Payment, Commission, Withdrawal)
- Search by transaction ID or username
- **Export as CSV** button for accounting
- Pagination support

**B. Pending Withdrawals**
- List of user withdrawal requests
- **Approve** to process the withdrawal
- **Reject** to decline the request
- Shows user, amount, and request date

**C. Commission Settings**
- Set commission rates for different transaction types:
  - Product Sales Commission
  - Service Commission
  - Subscription Fee
- Update rates and click "Save Changes"
- View current rates next to new rate inputs

### 5. **Settings**
Manage admin account and app settings:

**Profile Settings**:
- Update your name and email
- Click "Save Profile" to apply changes

**Security Settings**:
- Change your password
- Enter current password
- Create new password (min 6 characters)
- Confirm new password
- Click "Change Password"

**App Settings**:
- Set the application name
- Configure default commission rate
- Click "Save Settings"

## 🎯 Key Features

### Search & Filter
On any table page:
1. Use the search box to find items (by name, email, title, etc.)
2. Use dropdown filters to narrow by status or type
3. Results update instantly

### Pagination
At the bottom of tables:
- View items per page (10, 25, or 50)
- Navigate with Previous/Next buttons
- See current position (e.g., "1-10 of 50")

### Status Indicators
Color-coded badges show status at a glance:
- 🟡 **Yellow** = Pending (awaiting review)
- 🟢 **Green** = Approved/Active/Completed
- 🔴 **Red** = Rejected/Inactive/Failed

### Quick Actions
In-table action buttons:
- **👁️ View** = See full details
- **✓ Approve** = Accept (for posts/withdrawals)
- **✕ Reject** = Decline (for posts/withdrawals)
- **⏸ Suspend** = Disable user account

### Notifications
Green/red toast messages appear when you:
- Approve or reject a post
- Suspend or activate a user
- Approve or reject a withdrawal
- Save settings or changes

## 💡 Tips & Tricks

1. **Quick Navigation**: Click sidebar items to jump between sections
2. **Responsive Design**: Works on mobile, tablet, and desktop
3. **Dark Theme**: Purple (#6200EE) and Teal (#03DAC6) color scheme matches your Flutter app
4. **Time Display**: Current time shows in top-right header
5. **Logout Anytime**: Click "Logout" button in sidebar footer

## 🔗 Navigation Links

From the landing page:
- **Features** - Scroll to features section
- **API Docs** - Links to API documentation
- **Login** - Scroll to login form
- **Admin Dashboard** - Go directly to dashboard

## 🎨 Color Guide

| Color | Use | Hex Code |
|-------|-----|----------|
| Purple | Primary actions, buttons | #6200EE |
| Teal | Accents, hovers | #03DAC6 |
| Green | Success, approvals | #4CAF50 |
| Red | Danger, rejections | #F44336 |
| Orange | Warning, pending | #FF9800 |
| Blue | Info messages | #2196F3 |

## ❓ Common Questions

**Q: How do I add real posts/users to the dashboard?**
A: Currently, the app uses mock/demo data. To connect to real data, update the API endpoints in `js/dashboard.js` and ensure your backend is running.

**Q: Can I export transaction data?**
A: Yes! On the Wallet tab, click "📥 Export as CSV" to download transactions as a spreadsheet.

**Q: How do I change the app name or commission rates?**
A: Go to Settings → App Settings and Commission Settings tabs. Changes are applied immediately.

**Q: What if I forget the login password?**
A: Demo mode uses: Email: `admin@mango.com`, Password: `password123`

**Q: Does the dashboard work offline?**
A: Yes, with demo data! It works without an internet connection. Real data requires backend connectivity.

**Q: How do I customize colors?**
A: Edit CSS variables in `css/styles.css` (`:root` section). All colors are defined there.

## 📱 Mobile View

The dashboard is fully responsive:
- **Desktop** (1200px+): Full layout with sidebar
- **Tablet** (768px+): Adjusted spacing and touch-friendly buttons
- **Mobile** (320px+): Stacked layout, horizontal scrolling for tables

Try resizing your browser or opening on a mobile device!

## 🚨 Troubleshooting

**Issue**: Page won't load
- **Solution**: Make sure you're using a local server, not opening the file directly

**Issue**: Data not showing
- **Solution**: Check browser console (F12) for errors, refresh the page

**Issue**: Login fails
- **Solution**: Use demo credentials: `admin@mango.com` / `password123`

**Issue**: Buttons don't work
- **Solution**: Check that JavaScript is enabled in your browser

## 📞 Support Resources

- **API Docs**: See links in the landing page
- **Backend Setup**: Check Django/backend documentation
- **Frontend Issues**: Review the README.md file for detailed docs
- **Color Reference**: Check the CSS variables in `css/styles.css`

---

**You're all set! Happy admining! 🎉**

For detailed technical documentation, see [README.md](README.md)
