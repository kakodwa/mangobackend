from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Count, Q
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django_filters.rest_framework import DjangoFilterBackend

from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Shop, ShopReview
from .serializers import ShopSerializer, ShopCreateUpdateSerializer, ShopReviewSerializer


def download_app_view(request):
    return render(request, 'download_app.html')


def shop_qr_redirect(request, pk):
    shop = get_object_or_404(Shop, pk=pk)

    # Increment scan count metrics
    shop.qr_scan_count += 1
    shop.save(update_fields=["qr_scan_count"])

    # Redirect to FLUTTER web deployment or custom App Scheme.
    frontend_domain = "https://malatrade.com"
    return redirect(f"{frontend_domain}/shop/{shop.id}")


class ShopViewSet(viewsets.ModelViewSet):
    queryset = Shop.objects.filter(
        status='approved',
        is_active=True
    ).annotate(
        product_count=Count('products')
    )
    serializer_class = ShopSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'city', 'district']
    search_fields = ['name', 'description', 'category']
    ordering_fields = ['rating', 'created_at', 'name']

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return ShopCreateUpdateSerializer
        return ShopSerializer

    def _send_shop_creation_emails(self, shop):
        """
        Sends application receipt email to shop owner and alert to admin.
        """
        owner = getattr(shop, 'owner', None) or getattr(shop, 'user', None)
        if not owner or not getattr(owner, 'email', None):
            return

        owner_email = owner.email
        owner_name = getattr(owner, 'first_name', None) or getattr(owner, 'username', 'Vendor')
        shop_name = getattr(shop, 'name', 'Your Shop')

        # 1. Email to Shop Owner
        subject = f"MalaTrade: Shop Application Received [{shop_name}]"
        context = {
            'owner_name': owner_name,
            'shop_name': shop_name,
        }

        html_message = render_to_string('emails/shop_application_owner.html', context)
        plain_message = (
            f"Hello {owner_name},\n\n"
            f"Thank you for submitting your shop application for '{shop_name}' on MalaTrade!\n"
            f"Your application is currently under review by our support team.\n\n"
            f"Best regards,\nMalaTrade Support Team"
        )

        try:
            send_mail(
                subject=subject,
                message=plain_message,
                from_email="support@malatrade.com",
                recipient_list=[owner_email],
                html_message=html_message,
                fail_silently=False,
            )
        except Exception as e:
            print(f"[Shop Email] Owner email dispatch failed: {e}")

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Assign request.user as the owner if serializer doesn't handle it
        shop = serializer.save(owner=request.user) if hasattr(Shop, 'owner') else serializer.save()

        # 📧 Send confirmation email to vendor
        self._send_shop_creation_emails(shop)

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get'])
    def related(self, request, pk=None):
        shop = self.get_object()

        related_shops = Shop.objects.filter(
            status='approved',
            is_active=True
        ).exclude(
            id=shop.id
        ).filter(
            Q(category=shop.category) |
            Q(district=shop.district) |
            Q(city=shop.city)
        ).annotate(product_count=Count('products')
        ).order_by('-rating', '-product_count')[:10]

        serializer = self.get_serializer(related_shops, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def reviews(self, request, pk=None):
        shop = self.get_object()
        reviews = shop.reviews.all()
        serializer = ShopReviewSerializer(reviews, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def add_review(self, request, pk=None):
        shop = self.get_object()
        serializer = ShopReviewSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save(shop=shop)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def my_shops(self, request):
        shops = Shop.objects.filter(owner=request.user).annotate(product_count=Count('products'))
        serializer = ShopSerializer(shops, many=True)
        return Response(serializer.data)