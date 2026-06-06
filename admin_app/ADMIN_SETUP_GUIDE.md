# Django Admin Dashboard Setup Guide

## Installation Steps

### 1. Update Your Django Settings

Add the following to your `settings.py`:

```python
# Add admin templates to TEMPLATES
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR, 'templates'),  # Add your templates dir
            os.path.join(BASE_DIR, 'public'),     # Add public folder for static files
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# Static files configuration
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'public'),
]

# Media files for uploads
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
```

### 2. Update Your Main URLs

In your main project `urls.py`:

```python
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # ... your other paths
    path('admin-dashboard/', include('admin_urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
```

### 3. Copy Template Files

Copy the HTML files from `/public/` to your templates directory:

```bash
mkdir -p templates/admin
cp public/*.html templates/admin/
```

Update references in the HTML files:
- Change `script.js` to `{% static 'script.js' %}`
- Change `styles.css` to `{% static 'styles.css' %}`

### 4. Create Templates Directory Structure

```
templates/
├── admin/
│   ├── index.html          (dashboard)
│   ├── users.html
│   ├── shops.html
│   ├── products.html
│   ├── properties.html
│   ├── deliveries.html
│   ├── reviews.html
│   ├── lodges.html
│   ├── rooms.html
│   ├── bookings.html
│   ├── events.html
│   └── tickets.html
└── base.html               (optional base template)
```

### 5. Update View Functions

The views expect HTML templates. Make sure to:

1. Create a base template for shared styling
2. Update each template to use Django template syntax:
   - `{% load static %}`
   - `{{ variable_name }}`
   - `{% for item in items %}`
   - `{% if condition %}`

### 6. Add Required Models Import

Ensure your `models.py` files are properly set up in these apps:
- `users` - User, Address models
- `shops` - Shop, ShopReview models
- `products` - Product, ProductReview, ProductImage models
- `realestate` - Property, PropertyImage, PropertyUnlock models
- `deliveries` - Delivery, DeliveryPerson, DeliveryRating models
- `lodges` - Lodge, Room, Booking, Review, Amenity models
- `events` - Event, EventTicketType, Ticket, TicketCheckIn models

### 7. Run Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 8. Create Super User (if not already done)

```bash
python manage.py createsuperuser
```

## API Endpoints

### Dashboard Statistics
- **GET** `/admin-dashboard/api/statistics/` - Returns JSON with all statistics

### Users Management
- **GET** `/admin-dashboard/users/` - List all users
- **POST** `/admin-dashboard/users/<user_id>/verify/` - Verify user
- **POST** `/admin-dashboard/users/<user_id>/suspend/` - Suspend user
- **POST** `/admin-dashboard/users/<user_id>/activate/` - Activate user

### Shops Management
- **GET** `/admin-dashboard/shops/` - List shops
- **POST** `/admin-dashboard/shops/<shop_id>/approve/` - Approve shop
- **POST** `/admin-dashboard/shops/<shop_id>/reject/` - Reject shop
- **POST** `/admin-dashboard/shops/<shop_id>/suspend/` - Suspend shop
- **POST** `/admin-dashboard/shops/<shop_id>/activate/` - Activate shop

### Products Management
- **GET** `/admin-dashboard/products/` - List products
- **POST** `/admin-dashboard/products/<product_id>/activate/` - Activate product
- **POST** `/admin-dashboard/products/<product_id>/deactivate/` - Deactivate product

### Properties Management
- **GET** `/admin-dashboard/properties/` - List properties
- **POST** `/admin-dashboard/properties/<property_id>/approve/` - Approve property
- **POST** `/admin-dashboard/properties/<property_id>/reject/` - Reject property

### Deliveries Management
- **GET** `/admin-dashboard/deliveries/` - List deliveries
- **POST** `/admin-dashboard/deliveries/<delivery_id>/assign/` - Assign delivery
- **POST** `/admin-dashboard/deliveries/<delivery_id>/mark_delivered/` - Mark delivered

### Reviews Management
- **GET** `/admin-dashboard/reviews/` - List reviews
- **POST** `/admin-dashboard/reviews/<review_id>/delete/` - Delete review
- **POST** `/admin-dashboard/reviews/<review_id>/flag/` - Flag review

### Lodges Management
- **GET** `/admin-dashboard/lodges/` - List lodges
- **POST** `/admin-dashboard/lodges/<lodge_id>/verify/` - Verify lodge
- **POST** `/admin-dashboard/lodges/<lodge_id>/unverify/` - Unverify lodge

### Rooms Management
- **GET** `/admin-dashboard/rooms/` - List rooms

### Bookings Management
- **GET** `/admin-dashboard/bookings/` - List bookings
- **POST** `/admin-dashboard/bookings/<booking_id>/confirm/` - Confirm booking
- **POST** `/admin-dashboard/bookings/<booking_id>/cancel/` - Cancel booking

### Events Management
- **GET** `/admin-dashboard/events/` - List events
- **POST** `/admin-dashboard/events/<event_id>/publish/` - Publish event
- **POST** `/admin-dashboard/events/<event_id>/feature/` - Feature event
- **POST** `/admin-dashboard/events/<event_id>/unfeature/` - Unfeature event
- **POST** `/admin-dashboard/events/<event_id>/cancel/` - Cancel event

### Tickets Management
- **GET** `/admin-dashboard/tickets/` - List tickets
- **POST** `/admin-dashboard/tickets/<ticket_id>/mark_paid/` - Mark ticket as paid
- **POST** `/admin-dashboard/tickets/<ticket_id>/cancel/` - Cancel ticket

## Authentication & Authorization

All views require:
1. User to be logged in (`@login_required`)
2. User must be admin (`user_type='admin'`)

The `@admin_required` decorator enforces this. Unauthorized users get a 403 Forbidden response.

## Template Variables Available

### Dashboard View
- `total_users` - Total user count
- `total_shops` - Total shops count
- `pending_shops` - Shops awaiting approval
- `approved_shops` - Approved shops
- `total_products` - Total products
- `pending_deliveries` - Pending deliveries
- `recent_shops` - Last 5 shops created
- `recent_bookings` - Last 5 bookings
- `recent_events` - Last 5 events

### List Views
All list views pass their respective objects:
- `users` - User queryset with filters applied
- `shops` - Shop queryset with filters applied
- `products` - Product queryset with filters applied
- `properties` - Property queryset with filters applied
- `deliveries` - Delivery queryset with filters applied
- `reviews` - Review queryset with filters applied
- `lodges` - Lodge queryset with filters applied
- `rooms` - Room queryset with filters applied
- `bookings` - Booking queryset with filters applied
- `events` - Event queryset with filters applied
- `tickets` - Ticket queryset with filters applied

## Security Considerations

1. **Admin Only Access**: All views require admin user status
2. **CSRF Protection**: All POST requests use Django's CSRF token
3. **Database Queries**: Use `get_object_or_404` to prevent information leakage
4. **Input Validation**: All user inputs are validated through Django ORM
5. **Audit Trail**: Consider adding an audit log for admin actions

## Customization

### Adding New Admin Actions

1. Create a new function in `admin_views.py`:

```python
@login_required
@admin_required
@require_http_methods(["POST"])
def my_custom_action(request, item_id):
    item = get_object_or_404(MyModel, id=item_id)
    # Your logic here
    return JsonResponse({'success': True})
```

2. Add URL pattern in `admin_urls.py`:

```python
path('items/<int:item_id>/custom/', admin_views.my_custom_action, name='custom_action'),
```

3. Update template with action button

### Adding New Models

Simply import the model in `admin_views.py` and create list/action functions following the existing pattern.

## Performance Tips

1. Use `select_related()` for ForeignKey relationships
2. Use `prefetch_related()` for ManyToMany relationships
3. Add pagination for large querysets
4. Use Django's cache framework for statistics
5. Index frequently filtered fields in models

## Troubleshooting

**Templates not found?**
- Ensure `TEMPLATES['DIRS']` includes your templates directory
- Check template file names match exactly

**Admin access denied?**
- Verify user has `user_type='admin'`
- Check if user is superuser (optional enhancement)

**Models not found?**
- Verify app names in imports match your Django apps
- Run migrations: `python manage.py migrate`

**Static files not loading?**
- Run: `python manage.py collectstatic`
- Check `STATIC_URL` and `STATIC_ROOT` settings