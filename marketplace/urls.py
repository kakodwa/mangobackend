from django.contrib import admin
from django.urls import path, include, re_path
from django.views.generic import TemplateView
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from users.views import UserViewSet
from shops.views import ShopViewSet
from products.views import ProductViewSet, BannerViewSet
from orders.views import OrderViewSet
from payments.views import PaymentViewSet, paychangu_webhook, payment_return_view
from hospitality.views import LodgeViewSet, RoomViewSet, BookingViewSet, AmenityViewSet
from mangohub.views import ReviewViewSet
from events.views import EventViewSet, TicketViewSet, TicketValidationViewSet, TicketCheckInAPIView
from delivery.views import DeliveryViewSet
from realestate.views import PropertyViewSet
from wallet.views import WalletViewSet
from django.conf import settings
from django.conf.urls.static import static
from mangohub import views
from products.cj_views import ProductListView,ProductDetailView
from django.http import JsonResponse


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
router.register(r'reviews', ReviewViewSet, basename='reviews')
router.register(r'ticket-validation', TicketValidationViewSet, basename='ticket-validation')


# ===================================================================================
# 📱 MOBILE APP LINK VERIFICATION LOGIC (Android Assetlinks & iOS App Association)
# ===================================================================================
def serve_android_assetlinks(request):
    data = [
        {
            "relation": ["delegate_permission/common.handle_all_urls"],
            "target": {
                "namespace": "android_app",
                # 🌟 TODO: Verify this matches your application's package id inside android/app/build.gradle
                "package_name": "com.mangochi.marketplace", 
                # 🌟 TODO: Replace this with your actual release SHA-256 fingerprint certificate string
                "sha256_cert_fingerprints": [
                    "00:11:22:33:44:55:66:77:88:99:AA:BB:CC:DD:EE:FF:GG:HH:II:JJ:KK:LL:MM:NN:OO:PP:QQ:RR:SS:TT"
                ]
            }
        }
    ]
    return JsonResponse(data, safe=False)

def serve_ios_apple_association(request):
    data = {
        "applinks": {
            "apps": [],
            "details": [
                {
                    # 🌟 TODO: Replace "YOUR_APPLE_TEAM_ID" with your 10-character Apple Developer Team ID
                    "appID": "YOUR_APPLE_TEAM_ID.com.mangochi.marketplace",
                    "components": [
                        { "/": "/shop/*" },
                        { "/": "/product/*" },
                        { "/": "/lodge/*" },
                        { "/": "/event/*" }
                    ]
                }
            ]
        }
    }
    return JsonResponse(data)


urlpatterns = [
    # =================================================================
    # 📱 0. MOBILE APP LINK HANDLERS (Placed high up for instant discovery)
    # =================================================================
    path('.well-known/assetlinks.json', serve_android_assetlinks),
    path('.well-known/apple-app-site-association', serve_ios_apple_association),

    path('admin/', admin.site.urls),

    # =================================================================
    # 🎯 1. HIGH-PRIORITY EXPLICIT PAYMENT VIEWS (Checked First)
    # =================================================================
    path('api/payments/webhook/paychangu/', paychangu_webhook, name='paychangu_webhook'),
    path('api/payments/payment/return/', payment_return_view, name='payment_return_view'),

    path('payments/webhook/paychangu/', paychangu_webhook, name='paychangu_webhook_fallback'),
    path('payments/payment/return/', payment_return_view, name='payment_return_fallback'),
    

    # =================================================================
    # 🔌 2. STANDARD FEATURE API ENDPOINTS
    # =================================================================
    path('api/analytics/', include('analytics.urls')),

    path("api/cj/products/",ProductListView.as_view()),
    path("api/cj/products/<str:pid>/",ProductDetailView.as_view()),
    
    path('api/tickets/check-in/', TicketCheckInAPIView.as_view(), name='ticket-checkin'),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/password_reset/', include('django_rest_passwordreset.urls', namespace='password_reset')),
    path("api/feed/", include("feed_engine.urls")),
    path("admin_app", include("admin_app.urls")),
    path("", include("shops.urls")),
    
    # =================================================================
    # 🗂️ 3. CATCH-ALL ROUTER INCLUDE (Checked Last)
    # =================================================================
    path('api/', include(router.urls)),
    re_path(r'^(?!api/|admin/|payments/|\.well-known/).*$', views.serve_flutter_web_app, name='flutter_web_catchall'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)