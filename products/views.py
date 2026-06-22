from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import Product, ProductImage, ProductReview, Banner, AppVersion, Favorite
from .serializers import ProductSerializer, FavoriteSerializer, BannerSerializer, ProductImageSerializer, ProductCreateUpdateSerializer, ProductReviewSerializer
from rest_framework.filters import BaseFilterBackend
from .filters import DistrictFilterBackend
from django.db.models import Q
import json  # 👈 Added to safely parse the incoming text JSON string values


class BannerViewSet(ReadOnlyModelViewSet):
    queryset = Banner.objects.filter(is_active=True).order_by('-created_at')
    serializer_class = BannerSerializer


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.filter(is_active=True).select_related('shop')
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter, DistrictFilterBackend]
    filterset_fields = ['shop', 'shop__category', 'shop__district']
    search_fields = ['name', 'description', 'sku']
    ordering_fields = ['price', 'rating', 'created_at']

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return ProductCreateUpdateSerializer
        return ProductSerializer

    def create(self, request, *args, **kwargs):
        # 1. Convert QueryDict to a standard Python dict so nested arrays parse cleanly
        data = {key: value for key, value in request.data.items()}

        # 2. Intercept variants text block string from multipart and decode it back to native Python objects
        if 'variants' in data and isinstance(data['variants'], str):
            try:
                data['variants'] = json.loads(data['variants'])
            except json.JSONDecodeError:
                return Response(
                    {"variants": ["Invalid JSON format string received for variations entry."]},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # 3. Pass massaged payload structure data down to the write serializer
        serializer = self.get_serializer(data=data)
        if not serializer.is_valid():
            print("VALIDATION ERRORS:", serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        product = serializer.save(is_active=True)

        # Render outbound response layout using your presentation structure schema
        output_serializer = ProductSerializer(
            product,
            context={'request': request}
        )
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        # Handle update workflows similarly to convert QueryDict data safely
        data = {key: value for key, value in request.data.items()}

        if 'variants' in data and isinstance(data['variants'], str):
            try:
                data['variants'] = json.loads(data['variants'])
            except json.JSONDecodeError:
                return Response({"variants": ["Invalid JSON format structure configuration."]}, status=status.HTTP_400_BAD_REQUEST)

        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=data, partial=partial)
        if not serializer.is_valid():
            print("UPDATE VALIDATION ERRORS:", serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        product = serializer.save()
        output_serializer = ProductSerializer(product, context={'request': request})
        return Response(output_serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'])
    def reviews(self, request, pk=None):
        product = self.get_object()
        reviews = product.reviews.all()
        serializer = ProductReviewSerializer(reviews, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'], permission_classes=[permissions.AllowAny])
    def related(self, request, pk=None):
        product = self.get_object()

        related = Product.objects.filter(
            is_active=True
        ).filter(
            Q(category=product.category) |
            Q(shop=product.shop)
        ).exclude(id=product.id).order_by('-rating')[:12]

        serializer = ProductSerializer(
            related,
            many=True,
            context={'request': request})

        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def add_review(self, request, pk=None):
        product = self.get_object()
        serializer = ProductReviewSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save(product=product)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def toggle_favorite(self, request, pk=None):
        product = self.get_object()
        user = request.user
        favorite = Favorite.objects.filter(user=user, product=product).first()

        if favorite:
            favorite.delete()
            return Response({"favorite": False, "message": "Removed from favorites"})

        Favorite.objects.create(user=user, product=product)
        return Response({"favorite": True, "message": "Added to favorites"})

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def my_favorites(self, request):
        favorites = Favorite.objects.filter(user=request.user)
        serializer = FavoriteSerializer(favorites, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def my_products(self, request):
        products = Product.objects.filter(shop__owner=request.user)
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], parser_classes=[MultiPartParser, FormParser])
    def add_images(self, request, pk=None):
        product = self.get_object()

        print("\n🔥 ===== ADD IMAGES DEBUG =====")
        print("🔥 Content-Type:", request.content_type)
        print("🔥 POST DATA:", request.POST)
        print("🔥 FILES RAW:", request.FILES)
        print("🔥 FILES KEYS:", list(request.FILES.keys()))
        print("🔥 FILE COUNT:", len(request.FILES.getlist('images')))
        print("🔥 ============================\n")

        images = request.FILES.getlist('images')
        if not images:
            print("❌ NO IMAGES RECEIVED")
            return Response({"error": "No images received"}, status=400)

        saved = []
        for img in images:
            obj = ProductImage.objects.create(product=product, image=img)
            saved.append(obj.id)
            print("✅ SAVED IMAGE ID:", obj.id)

        return Response({"status": "success", "saved_images": saved})

    @action(detail=False, methods=['get'], permission_classes=[permissions.AllowAny])
    def app_version(self, request):
        version = AppVersion.objects.filter(is_active=True).order_by('-id').first()

        if not version:
            return Response({
                "latest_version": None,
                "force_update": False,
                "maintenance_mode": False,
                "message": None,
                "update_url": None
            })

        return Response({
            "latest_version": version.version,
            "force_update": version.force_update,
            "maintenance_mode": version.maintenance_mode,
            "message": version.message,
            "update_url": version.update_url
        })