# Template Integration Guide

## Overview

This guide shows how to integrate Django views with your HTML dashboard templates.

## Step 1: Set Up Django Template Syntax

### Update index.html (Dashboard)

Replace the static HTML with Django template tags:

```html
{% load static %}
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Admin Dashboard</title>
    <link rel="stylesheet" href="{% static 'styles.css' %}">
</head>
<body>
    <div class="container">
        <!-- Sidebar with navigation -->
        <aside class="sidebar">
            <div class="logo">
                <h2>Admin Panel</h2>
            </div>
            <ul class="nav-menu">
                <li><a href="{% url 'admin:dashboard' %}" class="active">📊 Dashboard</a></li>
                <li><a href="{% url 'admin:users_list' %}">👥 Users</a></li>
                <li><a href="{% url 'admin:shops_list' %}">🏪 Shops</a></li>
                <li><a href="{% url 'admin:products_list' %}">📦 Products</a></li>
                <li><a href="{% url 'admin:properties_list' %}">🏠 Properties</a></li>
                <li><a href="{% url 'admin:deliveries_list' %}">🚚 Deliveries</a></li>
                <li><a href="{% url 'admin:reviews_list' %}">⭐ Reviews</a></li>
                <li><a href="{% url 'admin:lodges_list' %}">🏨 Lodges</a></li>
                <li><a href="{% url 'admin:rooms_list' %}">🛏️ Rooms</a></li>
                <li><a href="{% url 'admin:bookings_list' %}">📅 Bookings</a></li>
                <li><a href="{% url 'admin:events_list' %}">🎪 Events</a></li>
                <li><a href="{% url 'admin:tickets_list' %}">🎫 Tickets</a></li>
            </ul>
        </aside>

        <!-- Main Content -->
        <div class="main-content">
            <header class="top-bar">
                <button class="menu-toggle" id="menuToggle">☰</button>
                <h1>Dashboard Overview</h1>
                <div class="user-profile">
                    <span>{{ user.get_full_name }}</span>
                    <img src="{% static 'profile-placeholder.jpg' %}" alt="Profile">
                </div>
            </header>

            <div class="content">
                <!-- Statistics Grid -->
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-icon">👥</div>
                        <div class="stat-info">
                            <h3>Total Users</h3>
                            <div class="stat-number">{{ total_users }}</div>
                        </div>
                    </div>

                    <div class="stat-card">
                        <div class="stat-icon">🏪</div>
                        <div class="stat-info">
                            <h3>Total Shops</h3>
                            <div class="stat-number">{{ total_shops }}</div>
                            <small>{{ pending_shops }} pending</small>
                        </div>
                    </div>

                    <div class="stat-card">
                        <div class="stat-icon">📦</div>
                        <div class="stat-info">
                            <h3>Total Products</h3>
                            <div class="stat-number">{{ total_products }}</div>
                        </div>
                    </div>

                    <div class="stat-card">
                        <div class="stat-icon">🏠</div>
                        <div class="stat-info">
                            <h3>Properties</h3>
                            <div class="stat-number">{{ total_properties }}</div>
                        </div>
                    </div>

                    <div class="stat-card">
                        <div class="stat-icon">🚚</div>
                        <div class="stat-info">
                            <h3>Deliveries</h3>
                            <div class="stat-number">{{ total_deliveries }}</div>
                            <small>{{ pending_deliveries }} pending</small>
                        </div>
                    </div>

                    <div class="stat-card">
                        <div class="stat-icon">🏨</div>
                        <div class="stat-info">
                            <h3>Lodges</h3>
                            <div class="stat-number">{{ total_lodges }}</div>
                        </div>
                    </div>

                    <div class="stat-card">
                        <div class="stat-icon">📅</div>
                        <div class="stat-info">
                            <h3>Bookings</h3>
                            <div class="stat-number">{{ total_bookings }}</div>
                        </div>
                    </div>

                    <div class="stat-card">
                        <div class="stat-icon">🎪</div>
                        <div class="stat-info">
                            <h3>Events</h3>
                            <div class="stat-number">{{ total_events }}</div>
                        </div>
                    </div>
                </div>

                <!-- Recent Activity Section -->
                <div class="section-card">
                    <h2>Recent Shops</h2>
                    <table class="data-table">
                        <thead>
                            <tr>
                                <th>Shop Name</th>
                                <th>Owner</th>
                                <th>Status</th>
                                <th>Created</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for shop in recent_shops %}
                            <tr>
                                <td>{{ shop.name }}</td>
                                <td>{{ shop.owner.username }}</td>
                                <td><span class="badge badge-{{ shop.status }}">{{ shop.get_status_display }}</span></td>
                                <td>{{ shop.created_at|date:"M d, Y" }}</td>
                                <td>
                                    <a href="{% url 'admin:shops_list' %}" class="btn-small">View</a>
                                </td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>

    <script src="{% static 'script.js' %}"></script>
</body>
</html>
```

## Step 2: Users List Template

```html
{% load static %}
<!DOCTYPE html>
<html>
<head>
    <title>Users Management</title>
    <link rel="stylesheet" href="{% static 'styles.css' %}">
</head>
<body>
    <div class="container">
        <!-- Sidebar -->
        <aside class="sidebar">
            <!-- ... navigation ... -->
        </aside>

        <div class="main-content">
            <header class="top-bar">
                <button class="menu-toggle" id="menuToggle">☰</button>
                <h1>Users Management</h1>
                <div class="user-profile">
                    <span>{{ user.get_full_name }}</span>
                </div>
            </header>

            <div class="content">
                <!-- Search & Filter -->
                <div class="search-filter-bar">
                    <form method="get" class="filter-form">
                        <input type="text" name="search" placeholder="Search users..." value="{{ search }}" class="search-box">
                        
                        <select name="user_type" class="filter-select">
                            <option value="">All User Types</option>
                            <option value="customer" {% if user_type == 'customer' %}selected{% endif %}>Customer</option>
                            <option value="shop_owner" {% if user_type == 'shop_owner' %}selected{% endif %}>Shop Owner</option>
                            <option value="property_owner" {% if user_type == 'property_owner' %}selected{% endif %}>Property Owner</option>
                            <option value="admin" {% if user_type == 'admin' %}selected{% endif %}>Admin</option>
                        </select>

                        <select name="is_verified" class="filter-select">
                            <option value="">All Users</option>
                            <option value="true" {% if is_verified == 'true' %}selected{% endif %}>Verified</option>
                            <option value="false" {% if is_verified == 'false' %}selected{% endif %}>Not Verified</option>
                        </select>

                        <button type="submit" class="btn">Filter</button>
                    </form>
                </div>

                <!-- Users Table -->
                <div class="section-card">
                    <h2>Users List ({{ users.count }})</h2>
                    <table class="data-table">
                        <thead>
                            <tr>
                                <th>Username</th>
                                <th>Email</th>
                                <th>Phone</th>
                                <th>Type</th>
                                <th>Verified</th>
                                <th>Active</th>
                                <th>Joined</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for user in users %}
                            <tr>
                                <td data-label="Username">{{ user.username }}</td>
                                <td data-label="Email">{{ user.email }}</td>
                                <td data-label="Phone">{{ user.phone_number }}</td>
                                <td data-label="Type">{{ user.get_user_type_display }}</td>
                                <td data-label="Verified">
                                    {% if user.is_verified %}
                                        <span class="badge badge-success">✓ Verified</span>
                                    {% else %}
                                        <span class="badge badge-warning">Pending</span>
                                    {% endif %}
                                </td>
                                <td data-label="Active">
                                    {% if user.is_active %}
                                        <span class="badge badge-success">Active</span>
                                    {% else %}
                                        <span class="badge badge-danger">Suspended</span>
                                    {% endif %}
                                </td>
                                <td data-label="Joined">{{ user.date_joined|date:"M d, Y" }}</td>
                                <td data-label="Actions">
                                    <div class="action-buttons">
                                        {% if not user.is_verified %}
                                        <button class="btn-small btn-success" onclick="verifyUser({{ user.id }})">Verify</button>
                                        {% endif %}
                                        {% if user.is_active %}
                                        <button class="btn-small btn-danger" onclick="suspendUser({{ user.id }})">Suspend</button>
                                        {% else %}
                                        <button class="btn-small btn-success" onclick="activateUser({{ user.id }})">Activate</button>
                                        {% endif %}
                                    </div>
                                </td>
                            </tr>
                            {% empty %}
                            <tr>
                                <td colspan="8" style="text-align: center; padding: 20px;">No users found</td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>

    <script src="{% static 'script.js' %}"></script>
    <script>
        function verifyUser(userId) {
            fetch(`/admin-dashboard/users/${userId}/verify/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                }
            })
            .then(r => r.json())
            .then(data => {
                if (data.success) {
                    location.reload();
                } else {
                    alert(data.error);
                }
            });
        }

        function suspendUser(userId) {
            fetch(`/admin-dashboard/users/${userId}/suspend/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                }
            })
            .then(r => r.json())
            .then(data => {
                if (data.success) {
                    location.reload();
                }
            });
        }

        function activateUser(userId) {
            fetch(`/admin-dashboard/users/${userId}/activate/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                }
            })
            .then(r => r.json())
            .then(data => {
                if (data.success) {
                    location.reload();
                }
            });
        }
    </script>
</body>
</html>
```

## Step 3: Update Main URLs

In your main Django project `urls.py`:

```python
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('admin-dashboard/', include('admin_urls')),
    # ... your other URLs
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
```

## Step 4: CSRF Token Setup

Add this hidden input to all forms and near action buttons:

```html
{% csrf_token %}
```

Or get it from meta tag:

```html
<meta name="csrf-token" content="{{ csrf_token }}">
```

Then in JavaScript:

```javascript
const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
```

## Step 5: Template Context Variables

### Dashboard Variables
- `total_users` - int
- `total_shops` - int
- `pending_shops` - int
- `approved_shops` - int
- `total_products` - int
- `total_properties` - int
- `pending_properties` - int
- `total_deliveries` - int
- `pending_deliveries` - int
- `total_lodges` - int
- `verified_lodges` - int
- `total_bookings` - int
- `confirmed_bookings` - int
- `total_events` - int
- `published_events` - int
- `total_tickets` - int
- `paid_tickets` - int
- `recent_shops` - QuerySet
- `recent_bookings` - QuerySet
- `recent_events` - QuerySet

### List Page Variables
All list pages provide:
- `<item_name>` - QuerySet (users, shops, products, etc.)
- `<filter_name>` - Current filter value

## Step 6: Common Pattern Examples

### Approval Pattern (Shops)

```html
<div class="approval-panel">
    <h3>Shop Information</h3>
    <p><strong>Name:</strong> {{ shop.name }}</p>
    <p><strong>Owner:</strong> {{ shop.owner.get_full_name }}</p>
    <p><strong>Category:</strong> {{ shop.category }}</p>
    <p><strong>Location:</strong> {{ shop.city }}, {{ shop.district }}</p>
    
    {% if shop.status == 'pending' %}
    <div class="approval-buttons">
        <button class="btn btn-success" onclick="approveShop({{ shop.id }})">Approve</button>
        <button class="btn btn-danger" onclick="rejectShop({{ shop.id }})">Reject</button>
    </div>
    {% endif %}
</div>
```

### Status Badge Pattern

```html
<span class="badge badge-{{ object.status|lower }}">
    {{ object.get_status_display }}
</span>
```

### Action Buttons Pattern

```html
<div class="action-buttons">
    <button class="btn-small" onclick="viewItem({{ item.id }})">View</button>
    <button class="btn-small" onclick="editItem({{ item.id }})">Edit</button>
    <button class="btn-small btn-danger" onclick="deleteItem({{ item.id }})">Delete</button>
</div>
```

## Step 7: Form Integration

```html
<form method="get" class="filter-form">
    <input type="text" name="search" placeholder="Search..." value="{{ search }}">
    <select name="status">
        <option value="">All Statuses</option>
        <option value="pending" {% if status == 'pending' %}selected{% endif %}>Pending</option>
        <option value="approved" {% if status == 'approved' %}selected{% endif %}>Approved</option>
    </select>
    <button type="submit" class="btn">Filter</button>
</form>
```

## Step 8: Date Formatting

```html
<!-- Created date -->
{{ object.created_at|date:"M d, Y H:i" }}

<!-- Just date -->
{{ object.created_at|date:"M d, Y" }}

<!-- Time only -->
{{ object.created_at|time:"H:i" }}

<!-- Relative time -->
{{ object.created_at|timesince }} ago
```

## Step 9: Conditionals

```html
<!-- If/else -->
{% if object.is_active %}
    <span class="status-active">Active</span>
{% else %}
    <span class="status-inactive">Inactive</span>
{% endif %}

<!-- Multiple conditions -->
{% if object.status == 'pending' and object.is_verified %}
    <!-- Show something -->
{% elif object.status == 'approved' %}
    <!-- Show something else -->
{% endif %}
```

## Step 10: Loops & Empty States

```html
{% for item in items %}
    <tr>
        <td>{{ item.name }}</td>
        <td>{{ item.created_at|date:"M d, Y" }}</td>
    </tr>
{% empty %}
    <tr>
        <td colspan="2" style="text-align: center;">No items found</td>
    </tr>
{% endfor %}
```

## Testing Templates

Run Django development server:

```bash
python manage.py runserver
```

Then visit:
- `http://localhost:8000/admin-dashboard/`
- `http://localhost:8000/admin-dashboard/users/`
- `http://localhost:8000/admin-dashboard/shops/`

## Troubleshooting

**Undefined variable?**
- Ensure view passes the variable in context dict

**URL not resolving?**
- Check app_name is set in urls.py
- Use {% url 'app_name:view_name' %}

**CSRF token error?**
- Add {% csrf_token %} to forms
- Import csrf_exempt if needed

**Static files not loading?**
- Run: `python manage.py collectstatic`
- Check STATIC_URL setting
- Verify file exists in public/ directory