from django.shortcuts import render, get_object_or_404, redirect
from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import Shop, ShopReview
from django.db.models import Count, Q
from .serializers import ShopSerializer, ShopCreateUpdateSerializer, ShopReviewSerializer
from django.shortcuts import get_object_or_404, redirect



def download_app_view(request):
    return render (request,'download_app.html')



def shop_qr_redirect(request, pk):
    shop = get_object_or_404(Shop, pk=pk)

    # Increment scan count metrics
    shop.qr_scan_count += 1
    shop.save(update_fields=["qr_scan_count"])

    # Redirect to your FLUTTER web deployment or custom App Scheme.
    # For a professional setup on Web & Mobile cross-compatibility:
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

    def create(self, request, *args, **kwargs):


        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        self.perform_create(serializer)

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
