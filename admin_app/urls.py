from django.urls import path
from . import views as admin_views
from .views import AdminLoginView, admin_logout

app_name = 'admin_app'

urlpatterns = [
    
    path('admin_login/', AdminLoginView.as_view(), name='admin_login'),
    path('admin-portal/logout/', admin_logout, name='admin_logout'),
    # ============================================
    # DASHBOARD
    # ============================================
    path('admin-portal/', admin_views.dashboard_overview, name='dashboard'),
    path('api/statistics/', admin_views.api_statistics, name='api_statistics'),
    
    # ============================================
    # USERS MANAGEMENT
    # ============================================
    path('users/', admin_views.users_list, name='users_list'),
    path('users/<int:user_id>/<str:action>/', admin_views.user_action, name='user_action'),
    
    # ============================================
    # SHOPS MANAGEMENT
    # ============================================
    path('shops/', admin_views.shops_list, name='shops_list'),
    path('shops/<int:shop_id>/<str:action>/', admin_views.shop_action, name='shop_action'),
    
    # ============================================
    # PRODUCTS MANAGEMENT
    # ============================================
    path('products/', admin_views.products_list, name='products_list'),
    path('products/<int:product_id>/<str:action>/', admin_views.product_action, name='product_action'),
    
    # ============================================
    # PROPERTIES MANAGEMENT
    # ============================================
    path('properties/', admin_views.properties_list, name='properties_list'),
    path('properties/<int:property_id>/<str:action>/', admin_views.property_action, name='property_action'),
    
    # ============================================
    # DELIVERIES MANAGEMENT
    # ============================================
    path('deliveries/', admin_views.deliveries_list, name='deliveries_list'),
    path('deliveries/<int:delivery_id>/<str:action>/', admin_views.delivery_action, name='delivery_action'),
    
    # ============================================
    # REVIEWS MANAGEMENT
    # ============================================
    path('reviews/', admin_views.reviews_list, name='reviews_list'),
    path('reviews/<int:review_id>/<str:action>/', admin_views.review_action, name='review_action'),
    
    # ============================================
    # LODGES MANAGEMENT
    # ============================================
    path('lodges/', admin_views.lodges_list, name='lodges_list'),
    path('lodges/<int:lodge_id>/<str:action>/', admin_views.lodge_action, name='lodge_action'),
    
    # ============================================
    # ROOMS MANAGEMENT
    # ============================================
    path('rooms/', admin_views.rooms_list, name='rooms_list'),
    
    # ============================================
    # BOOKINGS MANAGEMENT
    # ============================================
    path('bookings/', admin_views.bookings_list, name='bookings_list'),
    path('bookings/<int:booking_id>/<str:action>/', admin_views.booking_action, name='booking_action'),
    
    # ============================================
    # EVENTS MANAGEMENT
    # ============================================
    path('events/', admin_views.events_list, name='events_list'),
    path('events/<int:event_id>/<str:action>/', admin_views.event_action, name='event_action'),
    
    # ============================================
    # TICKETS MANAGEMENT
    # ============================================
    path('tickets/', admin_views.tickets_list, name='tickets_list'),
    path('tickets/<int:ticket_id>/<str:action>/', admin_views.ticket_action, name='ticket_action'),
]