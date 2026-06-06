from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from users.views import UserViewSet
from shops.views import ShopViewSet
from products.views import ProductViewSet, BannerViewSet
from orders.views import OrderViewSet
from payments.views import PaymentViewSet, paychangu_webhook, payment_return_view
from hospitality.views import LodgeViewSet, RoomViewSet, BookingViewSet, AmenityViewSet
from events.views import EventViewSet, TicketViewSet, TicketValidationViewSet, TicketCheckInAPIView
from delivery.views import DeliveryViewSet
from realestate.views import PropertyViewSet
from wallet.views import WalletViewSet
from django.conf import settings
from django.conf.urls.static import static

# API Router
router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'shops', ShopViewSet, basename='shop')
router.register(r'products', ProductViewSet, basename='product')
router.register(r'orders', OrderViewSet, basename='order')
router.register(r'payments', PaymentViewSet, basename='payment') # Router automatically configures api/payments/
router.register(r'properties', PropertyViewSet, basename='property')
router.register(r'wallet', WalletViewSet, basename='wallet')
router.register(r'banners', BannerViewSet, basename='banners')
router.register(r'deliveries', DeliveryViewSet, basename='delivery')
router.register(r'lodges', LodgeViewSet, basename='lodges')
router.register(r'rooms', RoomViewSet)
router.register(r'amenities', AmenityViewSet, basename='amenities')
router.register(r'bookings', BookingViewSet, basename='bookings')
router.register(r'events', EventViewSet, basename='events')
router.register(r'tickets', TicketViewSet, basename='tickets')
router.register(r'ticket-validation', TicketValidationViewSet, basename='ticket-validation')

urlpatterns = [
    path('admin/', admin.site.urls),

    # =================================================================
    # 🎯 1. HIGH-PRIORITY EXPLICIT PAYMENT VIEWS (Checked First)
    # =================================================================
    # Standard complete explicit API endpoints
    path('api/payments/webhook/paychangu/', paychangu_webhook, name='paychangu_webhook'),
    path('api/payments/payment/return/', payment_return_view, name='payment_return_view'),

    # Fallback paths to process payments if PayChangu strips the '/api/' prefix context
    path('payments/webhook/paychangu/', paychangu_webhook, name='paychangu_webhook_fallback'),
    path('payments/payment/return/', payment_return_view, name='payment_return_fallback'),
    

    # =================================================================
    # 🔌 2. STANDARD FEATURE API ENDPOINTS
    # =================================================================
    path('api/analytics/', include('analytics.urls')),
    path('api/tickets/check-in/', TicketCheckInAPIView.as_view(), name='ticket-checkin'),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path("api/feed/", include("feed_engine.urls")),
    path("", include("admin_app.urls")),
    
    # =================================================================
    # 🗂️ 3. CATCH-ALL ROUTER INCLUDE (Checked Last)
    # =================================================================
    # This remains at the bottom so it handles automated ViewSet actions (like initiate_payment)
    path('api/', include(router.urls)),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)