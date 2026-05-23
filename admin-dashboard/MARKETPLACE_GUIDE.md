# Marketplace Guide - Mango Platform

This document explains the four core marketplaces in the Mango platform and how they are featured in the landing page and admin dashboard.

## Overview

Mango is a **multi-service marketplace platform** combining four distinct marketplaces in one unified app:

```
┌─────────────────────────────────────────────────┐
│         MANGO MARKETPLACE PLATFORM              │
├─────────────────────────────────────────────────┤
│                                                 │
│  🛍️ E-Commerce  │  🏠 Real Estate  │  🏨 Hotels  │  🎫 Events
│                                                 │
│  Shop products  │ Buy/Sell homes  │ Book stays │ Get Tickets
│  from sellers   │ and properties  │ & lodges   │ for events
│                                                 │
└─────────────────────────────────────────────────┘
```

## 1. E-Commerce Marketplace

### Purpose
A full-featured online shopping platform where buyers can browse and purchase products from verified sellers.

### Key Features
- **Product Browsing** - Search and filter products by category
- **Shopping Cart** - Add items and manage cart
- **Secure Checkout** - Multiple payment options
- **Order Tracking** - Real-time order status
- **Seller Ratings** - Reviews and ratings system
- **Delivery Management** - Track shipments

### Backend API Endpoints
```
GET    /api/shops/                  # List all shops
GET    /api/shops/{id}/             # Get shop details
GET    /api/products/               # List all products
GET    /api/products/{id}/          # Get product details
POST   /api/products/               # Create product (seller)
PUT    /api/products/{id}/          # Update product
DELETE /api/products/{id}/          # Delete product
GET    /api/categories/             # List categories
GET    /api/orders/                 # List orders
POST   /api/orders/                 # Create order
GET    /api/orders/{id}/            # Order details
```

### Admin Dashboard Controls
- Monitor all products and shops
- Approve/reject new product listings
- Suspend or ban problematic sellers
- View sales metrics and trends
- Process refunds and disputes

---

## 2. Real Estate Marketplace

### Purpose
A dedicated platform for buying, selling, and renting properties including homes, apartments, and commercial spaces.

### Key Features
- **Property Listings** - Browse houses, apartments, commercial spaces
- **Advanced Filtering** - Filter by location, price, amenities
- **Property Details** - Full descriptions, amenities, and images
- **Premium Features** - Unlock premium listings for detailed info
- **Reviews & Ratings** - Tenant and landlord feedback
- **Virtual Tours** - Image galleries and location details

### Backend API Endpoints
```
GET    /api/properties/             # List all properties
GET    /api/properties/{id}/        # Get property details
POST   /api/properties/             # Create listing
PUT    /api/properties/{id}/        # Update property
DELETE /api/properties/{id}/        # Delete property
GET    /api/amenities/              # List amenities
POST   /api/properties/{id}/unlock/ # Unlock premium listing
GET    /api/banners/                # Property banners/promos
```

### Admin Dashboard Controls
- Review new property listings
- Manage premium unlock system
- Monitor listing quality
- Handle disputes between buyers and sellers
- View market statistics

---

## 3. Hospitality Marketplace

### Purpose
A booking platform for lodges, hotels, guesthouses, and other accommodation services.

### Key Features
- **Lodge Browsing** - Search and filter lodges by location
- **Room Listings** - View available rooms with pricing
- **Amenities Display** - Rooms and lodge amenities
- **Availability Checking** - Real-time room availability
- **Online Booking** - Instant reservation system
- **Guest Reviews** - Ratings and feedback from guests

### Backend API Endpoints
```
GET    /api/lodges/                 # List all lodges
GET    /api/lodges/{id}/            # Get lodge details
POST   /api/lodges/                 # Create lodge (manager)
PUT    /api/lodges/{id}/            # Update lodge
GET    /api/rooms/                  # List all rooms
GET    /api/rooms/{id}/             # Get room details
POST   /api/rooms/                  # Add room
GET    /api/amenities/              # Amenities list
GET    /api/bookings/               # List bookings
POST   /api/bookings/               # Create booking
PUT    /api/bookings/{id}/          # Update booking status
```

### Admin Dashboard Controls
- Oversee all lodges and availability
- Monitor booking quality
- Handle cancellations and disputes
- Approve new lodge registrations
- View occupancy rates and revenue

---

## 4. Events & Ticketing Marketplace

### Purpose
A comprehensive event discovery and ticketing platform for concerts, conferences, sports events, and more.

### Key Features
- **Event Discovery** - Browse upcoming events
- **Categories & Filtering** - Filter by event type, date, location
- **Digital Tickets** - Instant ticket purchase and delivery
- **QR Verification** - Digital ticket validation at events
- **Ticket Management** - View owned tickets and history
- **Organizer Support** - Tools for event creators

### Backend API Endpoints
```
GET    /api/events/                 # List all events
GET    /api/events/{id}/            # Get event details
POST   /api/events/                 # Create event (organizer)
PUT    /api/events/{id}/            # Update event
GET    /api/tickets/                # List all tickets
GET    /api/tickets/{id}/           # Get ticket details
POST   /api/tickets/                # Purchase ticket
GET    /api/tickets/{id}/qr/        # Get QR code for ticket
```

### Admin Dashboard Controls
- Monitor event listings
- Verify event organizers
- Handle fraud and fake tickets
- Manage disputes
- View event metrics and attendance

---

## Landing Page Structure

The landing page showcases all four marketplaces with:

### Hero Section
```
Title: "Mango - Your All-in-One Marketplace"
Description: "Shop for anything, find your dream property, 
             book perfect stays, and discover amazing events—
             all in one app."
```

### Marketplaces Showcase (4 Cards)
Each marketplace has a dedicated card showing:
- 🛍️ E-Commerce - Products, carts, orders
- 🏠 Real Estate - Properties, locations, reviews
- 🏨 Hospitality - Lodges, rooms, bookings
- 🎫 Events - Events, tickets, passes

### Why Mango Section
Features that apply across all marketplaces:
- Secure Payments
- Trusted & Safe
- Fast & Responsive
- Rewards & Wallet
- Mobile & Web
- 24/7 Support

### How It Works
Six-step guide:
1. Download App
2. Create Account
3. Explore Marketplaces
4. Make Purchase
5. Track & Enjoy
6. Share Feedback

### Download Section
Links to download on:
- Apple App Store (iOS)
- Google Play Store (Android)
- Web Version

---

## Admin Dashboard Features by Marketplace

### E-Commerce Management
- Product approval queue
- Seller management
- Order monitoring
- Review fraud detection

### Real Estate Management
- Property listing review
- Premium unlock approvals
- Dispute resolution
- Market analytics

### Hospitality Management
- Lodge registration review
- Room management oversight
- Booking dispute handling
- Occupancy monitoring

### Events Management
- Event verification
- Organizer vetting
- Ticket fraud prevention
- Attendance tracking

---

## Digital Wallet Integration

All four marketplaces use a **unified Digital Wallet** system:

### Features
- Single wallet for all transactions
- Earn commissions from multiple services
- Track earnings and withdrawals
- Secure payment handling
- Multi-service balance

### Admin Control
- Set commission rates per marketplace
- Monitor wallet transactions
- Approve/reject withdrawals
- Generate financial reports

---

## Payment Integration

The platform supports multiple payment methods:

### Supported Payment Methods
1. **Airtel Money** - Mobile money payments
2. **TNM Mpamba** - Telecom payment service
3. **Bank Transfer** - Direct bank payments
4. **Wallet Balance** - Digital wallet payments
5. **Card Payments** - Credit/debit cards (future)

### Admin Dashboard
- Monitor all transactions
- Set commission rates
- View payment analytics
- Handle disputes

---

## Data Flow Example

Here's how a typical transaction flows through the system:

### E-Commerce Purchase
```
User → Browse Products → Add to Cart → Checkout
  ↓
Select Payment Method (Wallet/Mobile Money/Bank)
  ↓
Process Payment via Payment Service
  ↓
Create Order & Notify Seller
  ↓
Seller Fulfills Order
  ↓
Buyer Receives & Confirms
  ↓
Funds Released to Seller's Wallet
  ↓
Commission Deducted to Admin Wallet
```

### Property Listing
```
Agent → Create Listing → Add Details & Images
  ↓
Option to "Unlock Premium" for visibility
  ↓
Admin Approves Listing (Dashboard)
  ↓
Listing Goes Live
  ↓
Buyers Browse & Inquire
  ↓
Commission Applied on Sale
```

### Hotel Booking
```
Guest → Browse Lodges → Select Room & Dates
  ↓
Check Availability (Real-time)
  ↓
Proceed to Booking
  ↓
Make Payment
  ↓
Booking Confirmation
  ↓
Guest Receives Booking Details
  ↓
Check-in Day → Use Digital Key/Confirmation
  ↓
Stay Completed → Leave Review
```

### Event Ticket Purchase
```
User → Browse Events → Select Event & Date
  ↓
Choose Ticket Type & Quantity
  ↓
Add to Cart & Checkout
  ↓
Make Payment
  ↓
Instant Digital Ticket Delivery
  ↓
Show QR Code at Event
  ↓
Event Scanner Verifies Ticket
  ↓
User Enters Event
```

---

## Future Marketplace Opportunities

As Mango grows, consider adding:

1. **Service Marketplace** - Freelancers and service providers
2. **Food Delivery** - Restaurants and food ordering
3. **Education** - Courses and tutoring
4. **Automotive** - Car sales and rentals
5. **Healthcare** - Doctor appointments and services
6. **Job Board** - Job listings and recruitment

Each new marketplace would integrate with the same wallet, authentication, and payment system.

---

## Getting Started

### For Users
1. Download Mango from App Store or Google Play
2. Create an account
3. Start exploring the marketplaces
4. Make your first purchase/booking

### For Admin
1. Login to admin dashboard
2. Review content in each marketplace
3. Approve/reject listings
4. Monitor transactions
5. Manage commission rates

### For Developers
1. Review API endpoints for each marketplace
2. Implement frontend screens for each service
3. Integrate payment processing
4. Add real-time features (notifications, chat)
5. Build organizer/seller dashboards

---

## Summary

Mango is a **unified marketplace ecosystem** where:
- Users have one account for all services
- Sellers/organizers manage multiple marketplace types
- Admin dashboard controls all platforms from one place
- Wallet system connects all transactions
- Single authentication for seamless experience

This multi-service approach maximizes user engagement while providing a comprehensive business solution.
