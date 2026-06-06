from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db.models import Q, Count
from datetime import datetime, timedelta

# Models Import
from users.models import User, Address
from shops.models import Shop, ShopReview
from products.models import Product, ProductReview
from realestate.models import Property, PropertyUnlock
from delivery.models import Delivery, DeliveryPerson, DeliveryRating
from hospitality.models import Lodge, Room, Booking, Review as LodgeReview, Amenity
from events.models import Event, EventTicketType, Ticket, TicketCheckIn

from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.views import View

class AdminLoginView(View):
    template_name = 'admin/admin_login.html'

    def get(self, request):
        # If already authenticated as staff, skip login and go to dashboard
        if request.user.is_authenticated and request.user.is_staff:
            return redirect('admin_app:dashboard')
        return render(request, self.template_name)

    def post(self, request):
        # Extract credentials from your HTML form fields
        username_or_email = request.POST.get('username')
        password = request.POST.get('password')
        remember_me = request.POST.get('remember')

        # 1. Authenticate user credentials
        user = authenticate(request, username=username_or_email, password=password)

        if user is not None:
            # 2. Strict Guardrail: Verify administrative clearance
            if user.is_staff or user.is_superuser:
                login(request, user)
                
                # 3. Handle session expiry for 'Remember me' checkbox
                if not remember_me:
                    request.session.set_expiry(0) # Session expires when browser closes
                else:
                    request.session.set_expiry(1209600) # Session persists for 2 weeks
                
                messages.success(request, f"Welcome back, {user.username}!")
                return redirect('admin_app:dashboard') # Name of your dashboard URL route
            else:
                # Regular user trying to breach the admin panel portal
                messages.error(request, "Access Denied: Insufficient security clearance privileges.")
        else:
            # Invalid credentials
            messages.error(request, "Invalid identification identifier or security passphrase.")

        return render(request, self.template_name)

def admin_logout(request):
    logout(request)
    messages.info(request, "Logged out securely.")
    return redirect('admin_login')





# ============================================
# ADMIN PERMISSION CHECK
# ============================================
def is_admin(user):
    return user.is_authenticated and user.user_type == 'admin'

def admin_required(view_func):
    """Decorator to check if user is admin"""
    def wrapper(request, *args, **kwargs):
        if not is_admin(request.user):
            return JsonResponse({'error': 'Admin access required'}, status=403)
        return view_func(request, *args, **kwargs)
    return wrapper

# ============================================
# DASHBOARD OVERVIEW
# ============================================
@login_required
@admin_required
def dashboard_overview(request):
    """Main dashboard with statistics"""
    context = {
        'total_users': User.objects.count(),
        'total_shops': Shop.objects.count(),
        'pending_shops': Shop.objects.filter(status='pending').count(),
        'approved_shops': Shop.objects.filter(status='approved').count(),
        'total_products': Product.objects.count(),
        'total_properties': Property.objects.count(),
        'pending_properties': Property.objects.filter(status='available', is_publicly_visible=False).count(),
        'total_deliveries': Delivery.objects.count(),
        'pending_deliveries': Delivery.objects.filter(status='pending').count(),
        'total_lodges': Lodge.objects.count(),
        'verified_lodges': Lodge.objects.filter(is_verified=True).count(),
        'total_bookings': Booking.objects.count(),
        'confirmed_bookings': Booking.objects.filter(booking_status='confirmed').count(),
        'total_events': Event.objects.count(),
        'published_events': Event.objects.filter(status='published').count(),
        'total_tickets': Ticket.objects.count(),
        'paid_tickets': Ticket.objects.filter(payment_status='paid').count(),
    }
    
    # Recent activities
    context['recent_shops'] = Shop.objects.all()[:5]
    context['recent_bookings'] = Booking.objects.all()[:5]
    context['recent_events'] = Event.objects.all()[:5]
    
    return render(request, 'admin_app/index.html', context)

# ============================================
# USERS MANAGEMENT
# ============================================
@login_required
@admin_required
def users_list(request):
    """List all users with filters"""
    users = User.objects.all()
    
    # Filters
    user_type = request.GET.get('user_type')
    is_verified = request.GET.get('is_verified')
    search = request.GET.get('search')
    
    if user_type:
        users = users.filter(user_type=user_type)
    if is_verified:
        users = users.filter(is_verified=is_verified == 'true')
    if search:
        users = users.filter(
            Q(username__icontains=search) |
            Q(email__icontains=search) |
            Q(phone_number__icontains=search)
        )
    
    context = {
        'users': users,
        'user_type': user_type,
        'is_verified': is_verified,
        'search': search,
    }
    return render(request, 'admin_app/users.html', context)

@login_required
@admin_required
@require_http_methods(["POST"])
def user_action(request, user_id, action):
    """Handle user actions (verify, suspend, etc.)"""
    user = get_object_or_404(User, id=user_id)
    
    if action == 'verify':
        user.is_verified = True
        user.save()
        return JsonResponse({'success': True, 'message': 'User verified'})
    elif action == 'suspend':
        user.is_active = False
        user.save()
        return JsonResponse({'success': True, 'message': 'User suspended'})
    elif action == 'activate':
        user.is_active = True
        user.save()
        return JsonResponse({'success': True, 'message': 'User activated'})
    
    return JsonResponse({'error': 'Invalid action'}, status=400)

# ============================================
# SHOPS MANAGEMENT
# ============================================
@login_required
@admin_required
def shops_list(request):
    """List shops with approval workflow"""
    shops = Shop.objects.all()
    
    # Filters
    status = request.GET.get('status')
    search = request.GET.get('search')
    
    if status:
        shops = shops.filter(status=status)
    if search:
        shops = shops.filter(Q(name__icontains=search) | Q(owner__username__icontains=search))
    
    context = {
        'shops': shops,
        'status': status,
        'search': search,
    }
    return render(request, 'admin_app/shops.html', context)

@login_required
@admin_required
@require_http_methods(["POST"])
def shop_action(request, shop_id, action):
    """Handle shop approval/rejection"""
    shop = get_object_or_404(Shop, id=shop_id)
    
    if action == 'approve':
        shop.status = 'approved'
        shop.save()
        return JsonResponse({'success': True, 'message': 'Shop approved'})
    elif action == 'reject':
        shop.status = 'rejected'
        shop.save()
        return JsonResponse({'success': True, 'message': 'Shop rejected'})
    elif action == 'suspend':
        shop.status = 'suspended'
        shop.save()
        return JsonResponse({'success': True, 'message': 'Shop suspended'})
    elif action == 'activate':
        shop.status = 'approved'
        shop.is_active = True
        shop.save()
        return JsonResponse({'success': True, 'message': 'Shop activated'})
    
    return JsonResponse({'error': 'Invalid action'}, status=400)

# ============================================
# PRODUCTS MANAGEMENT
# ============================================
@login_required
@admin_required
def products_list(request):
    """List all products"""
    products = Product.objects.all()
    
    # Filters
    shop = request.GET.get('shop')
    status = request.GET.get('status')
    search = request.GET.get('search')
    
    if shop:
        products = products.filter(shop_id=shop)
    if status == 'low_stock':
        products = products.filter(stock__lt=10)
    elif status == 'out_of_stock':
        products = products.filter(stock=0)
    if search:
        products = products.filter(Q(name__icontains=search) | Q(sku__icontains=search))
    
    context = {
        'products': products,
        'shops': Shop.objects.all(),
        'status': status,
        'search': search,
    }
    return render(request, 'admin_app/products.html', context)

@login_required
@admin_required
@require_http_methods(["POST"])
def product_action(request, product_id, action):
    """Handle product actions"""
    product = get_object_or_404(Product, id=product_id)
    
    if action == 'deactivate':
        product.is_active = False
        product.save()
        return JsonResponse({'success': True, 'message': 'Product deactivated'})
    elif action == 'activate':
        product.is_active = True
        product.save()
        return JsonResponse({'success': True, 'message': 'Product activated'})
    
    return JsonResponse({'error': 'Invalid action'}, status=400)

# ============================================
# PROPERTIES MANAGEMENT
# ============================================
@login_required
@admin_required
def properties_list(request):
    """List real estate properties"""
    properties = Property.objects.all()
    
    # Filters
    status = request.GET.get('status')
    listing = request.GET.get('listing')
    search = request.GET.get('search')
    
    if status:
        properties = properties.filter(status=status)
    if listing:
        properties = properties.filter(listing_purpose=listing)
    if search:
        properties = properties.filter(Q(title__icontains=search) | Q(address__icontains=search))
    
    context = {
        'properties': properties,
        'status': status,
        'listing': listing,
        'search': search,
    }
    return render(request, 'admin_app/properties.html', context)

@login_required
@admin_required
@require_http_methods(["POST"])
def property_action(request, property_id, action):
    """Handle property approval"""
    property_obj = get_object_or_404(Property, id=property_id)
    
    if action == 'approve':
        property_obj.is_publicly_visible = True
        property_obj.save()
        return JsonResponse({'success': True, 'message': 'Property approved'})
    elif action == 'reject':
        property_obj.is_publicly_visible = False
        property_obj.save()
        return JsonResponse({'success': True, 'message': 'Property hidden'})
    
    return JsonResponse({'error': 'Invalid action'}, status=400)

# ============================================
# DELIVERIES MANAGEMENT
# ============================================
@login_required
@admin_required
def deliveries_list(request):
    """List all deliveries"""
    deliveries = Delivery.objects.all()
    
    # Filters
    status = request.GET.get('status')
    search = request.GET.get('search')
    
    if status:
        deliveries = deliveries.filter(status=status)
    if search:
        deliveries = deliveries.filter(Q(order__order_number__icontains=search))
    
    context = {
        'deliveries': deliveries,
        'status': status,
        'search': search,
    }
    return render(request, 'admin_app/deliveries.html', context)

@login_required
@admin_required
@require_http_methods(["POST"])
def delivery_action(request, delivery_id, action):
    """Handle delivery status updates"""
    delivery = get_object_or_404(Delivery, id=delivery_id)
    
    if action == 'assign':
        delivery.status = 'assigned'
        delivery.save()
        return JsonResponse({'success': True, 'message': 'Delivery assigned'})
    elif action == 'mark_delivered':
        delivery.status = 'delivered'
        delivery.delivered_at = datetime.now()
        delivery.save()
        return JsonResponse({'success': True, 'message': 'Delivery marked as delivered'})
    
    return JsonResponse({'error': 'Invalid action'}, status=400)

# ============================================
# REVIEWS MANAGEMENT
# ============================================
@login_required
@admin_required
def reviews_list(request):
    """List product and shop reviews"""
    reviews_type = request.GET.get('type', 'products')
    
    if reviews_type == 'products':
        reviews = ProductReview.objects.all()
    else:
        reviews = ShopReview.objects.all()
    
    # Filter flagged reviews
    flagged = request.GET.get('flagged')
    if flagged:
        reviews = reviews.filter(flagged=True) if hasattr(reviews.first(), 'flagged') else reviews
    
    context = {
        'reviews': reviews,
        'reviews_type': reviews_type,
        'flagged': flagged,
    }
    return render(request, 'admin_app/reviews.html', context)

@login_required
@admin_required
@require_http_methods(["POST"])
def review_action(request, review_id, action):
    """Handle review moderation"""
    review = get_object_or_404(ProductReview, id=review_id)
    
    if action == 'delete':
        review.delete()
        return JsonResponse({'success': True, 'message': 'Review deleted'})
    elif action == 'flag':
        # Add flag logic if needed
        return JsonResponse({'success': True, 'message': 'Review flagged'})
    
    return JsonResponse({'error': 'Invalid action'}, status=400)

# ============================================
# LODGES MANAGEMENT
# ============================================
@login_required
@admin_required
def lodges_list(request):
    """List accommodations/lodges"""
    lodges = Lodge.objects.all()
    
    # Filters
    verified = request.GET.get('verified')
    search = request.GET.get('search')
    
    if verified:
        lodges = lodges.filter(is_verified=verified == 'true')
    if search:
        lodges = lodges.filter(Q(name__icontains=search) | Q(owner__username__icontains=search))
    
    context = {
        'lodges': lodges,
        'verified': verified,
        'search': search,
    }
    return render(request, 'admin_app/lodges.html', context)

@login_required
@admin_required
@require_http_methods(["POST"])
def lodge_action(request, lodge_id, action):
    """Handle lodge verification"""
    lodge = get_object_or_404(Lodge, id=lodge_id)
    
    if action == 'verify':
        lodge.is_verified = True
        lodge.save()
        return JsonResponse({'success': True, 'message': 'Lodge verified'})
    elif action == 'unverify':
        lodge.is_verified = False
        lodge.save()
        return JsonResponse({'success': True, 'message': 'Lodge unverified'})
    
    return JsonResponse({'error': 'Invalid action'}, status=400)

# ============================================
# ROOMS MANAGEMENT
# ============================================
@login_required
@admin_required
def rooms_list(request):
    """List all rooms"""
    rooms = Room.objects.all()
    
    # Filters
    lodge = request.GET.get('lodge')
    room_type = request.GET.get('room_type')
    
    if lodge:
        rooms = rooms.filter(lodge_id=lodge)
    if room_type:
        rooms = rooms.filter(room_type=room_type)
    
    context = {
        'rooms': rooms,
        'lodges': Lodge.objects.all(),
        'lodge': lodge,
        'room_type': room_type,
    }
    return render(request, 'admin_app/rooms.html', context)

# ============================================
# BOOKINGS MANAGEMENT
# ============================================
@login_required
@admin_required
def bookings_list(request):
    """List lodge bookings"""
    bookings = Booking.objects.all()
    
    # Filters
    status = request.GET.get('status')
    payment_status = request.GET.get('payment_status')
    
    if status:
        bookings = bookings.filter(booking_status=status)
    if payment_status:
        bookings = bookings.filter(payment_status=payment_status)
    
    context = {
        'bookings': bookings,
        'status': status,
        'payment_status': payment_status,
    }
    return render(request, 'admin_app/bookings.html', context)

@login_required
@admin_required
@require_http_methods(["POST"])
def booking_action(request, booking_id, action):
    """Handle booking actions"""
    booking = get_object_or_404(Booking, id=booking_id)
    
    if action == 'confirm':
        booking.booking_status = 'confirmed'
        booking.save()
        return JsonResponse({'success': True, 'message': 'Booking confirmed'})
    elif action == 'cancel':
        booking.booking_status = 'cancelled'
        booking.save()
        return JsonResponse({'success': True, 'message': 'Booking cancelled'})
    
    return JsonResponse({'error': 'Invalid action'}, status=400)

# ============================================
# EVENTS MANAGEMENT
# ============================================
@login_required
@admin_required
def events_list(request):
    """List all events"""
    events = Event.objects.all()
    
    # Filters
    status = request.GET.get('status')
    is_featured = request.GET.get('featured')
    
    if status:
        events = events.filter(status=status)
    if is_featured:
        events = events.filter(is_featured=is_featured == 'true')
    
    context = {
        'events': events,
        'status': status,
        'is_featured': is_featured,
    }
    return render(request, 'admin_app/events.html', context)

@login_required
@admin_required
@require_http_methods(["POST"])
def event_action(request, event_id, action):
    """Handle event actions"""
    event = get_object_or_404(Event, id=event_id)
    
    if action == 'publish':
        event.status = 'published'
        event.save()
        return JsonResponse({'success': True, 'message': 'Event published'})
    elif action == 'feature':
        event.is_featured = True
        event.save()
        return JsonResponse({'success': True, 'message': 'Event featured'})
    elif action == 'unfeature':
        event.is_featured = False
        event.save()
        return JsonResponse({'success': True, 'message': 'Event unfeatured'})
    elif action == 'cancel':
        event.status = 'cancelled'
        event.save()
        return JsonResponse({'success': True, 'message': 'Event cancelled'})
    
    return JsonResponse({'error': 'Invalid action'}, status=400)

# ============================================
# TICKETS MANAGEMENT
# ============================================
@login_required
@admin_required
def tickets_list(request):
    """List event tickets"""
    tickets = Ticket.objects.all()
    
    # Filters
    event = request.GET.get('event')
    payment_status = request.GET.get('payment_status')
    
    if event:
        tickets = tickets.filter(event_id=event)
    if payment_status:
        tickets = tickets.filter(payment_status=payment_status)
    
    context = {
        'tickets': tickets,
        'events': Event.objects.all(),
        'event': event,
        'payment_status': payment_status,
    }
    return render(request, 'admin_app/tickets.html', context)

@login_required
@admin_required
@require_http_methods(["POST"])
def ticket_action(request, ticket_id, action):
    """Handle ticket actions"""
    ticket = get_object_or_404(Ticket, id=ticket_id)
    
    if action == 'mark_paid':
        ticket.payment_status = 'paid'
        ticket.save()
        return JsonResponse({'success': True, 'message': 'Ticket marked as paid'})
    elif action == 'cancel':
        ticket.payment_status = 'cancelled'
        ticket.save()
        return JsonResponse({'success': True, 'message': 'Ticket cancelled'})
    
    return JsonResponse({'error': 'Invalid action'}, status=400)

# ============================================
# API ENDPOINTS FOR DASHBOARD
# ============================================
@login_required
@admin_required
def api_statistics(request):
    """JSON endpoint for statistics"""
    stats = {
        'users': User.objects.count(),
        'shops': Shop.objects.count(),
        'products': Product.objects.count(),
        'pending_approvals': Shop.objects.filter(status='pending').count() + 
                             Property.objects.filter(is_publicly_visible=False).count(),
        'deliveries': {
            'pending': Delivery.objects.filter(status='pending').count(),
            'in_transit': Delivery.objects.filter(status='in_transit').count(),
            'delivered': Delivery.objects.filter(status='delivered').count(),
        },
        'bookings': {
            'total': Booking.objects.count(),
            'confirmed': Booking.objects.filter(booking_status='confirmed').count(),
            'pending': Booking.objects.filter(booking_status='pending').count(),
        },
        'events': {
            'total': Event.objects.count(),
            'published': Event.objects.filter(status='published').count(),
        },
    }
    return JsonResponse(stats)