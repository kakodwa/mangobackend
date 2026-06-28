from django.db.models import Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from hospitality.models import Lodge
from events.models import Event
from products.models import Product
from realestate.models import Property
from shops.models import Shop

from .serializers import UnifiedSearchItemSerializer
from .pagination import UnifiedSearchPagination


class UnifiedSearchView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request, *args, **kwargs):
        query = request.GET.get('q', '').strip()
        target_type = request.GET.get('type', 'all').strip().lower()
        
        district = request.GET.get('district', '').strip()
        category = request.GET.get('category', '').strip()
        listing_purpose = request.GET.get('listing_purpose', '').strip()

        combined_results = []

        # =========================================================
        # 1. PRODUCTS FILTERING
        # =========================================================
        if target_type in ['all', 'product']:
            products = Product.objects.filter(
                is_active=True, 
                shop__status='approved'
            ).select_related('shop').prefetch_related('variants')

            if query:
                products = products.filter(Q(name__icontains=query) | Q(description__icontains=query))
            if district: 
                products = products.filter(shop__district__iexact=district)
            if category and category.lower() != 'all': 
                products = products.filter(category__icontains=category)
            
            for item in products:
                item.result_type = 'product'
                item.title = item.name
                item.subtitle = item.description[:100] if item.description else ''
                item.city = item.shop.city
                item.district = item.shop.district
                combined_results.append(item)

        # =========================================================
        # 2. EVENTS FILTERING
        # =========================================================
        if target_type in ['all', 'event']:
            events = Event.objects.filter(status='published')
            if query:
                events = events.filter(Q(title__icontains=query) | Q(description__icontains=query))
            if district: 
                events = events.filter(district__iexact=district)
            
            for item in events:
                item.result_type = 'event'
                item.title = item.title
                item.subtitle = item.description[:100] if item.description else ''
                item.price = None
                combined_results.append(item)

        # =========================================================
        # 3. LODGES FILTERING
        # =========================================================
        if target_type in ['all', 'lodge']:
            lodges = Lodge.objects.filter(is_active=True)
            if query:
                lodges = lodges.filter(Q(name__icontains=query) | Q(description__icontains=query))
            if district: 
                lodges = lodges.filter(district__iexact=district)
            if category and category.lower() != 'all': 
                lodges = lodges.filter(lodge_type__icontains=category)
            
            for item in lodges:
                item.result_type = 'lodge'
                item.title = item.name
                item.subtitle = item.description[:100] if item.description else ''
                item.price = None
                combined_results.append(item)

        # =========================================================
        # 4. PROPERTIES FILTERING
        # =========================================================
        if target_type in ['all', 'property']:
            properties = Property.objects.filter(status='available', is_publicly_visible=True)
            if query:
                properties = properties.filter(Q(title__icontains=query) | Q(description__icontains=query))
            if district: 
                properties = properties.filter(district__iexact=district)
            if category and category.lower() != 'all': 
                properties = properties.filter(property_type__icontains=category)
            if listing_purpose and listing_purpose.lower() != 'all': 
                properties = properties.filter(listing_purpose__iexact=listing_purpose)

            for item in properties:
                item.result_type = 'property'
                item.title = item.title  # ✅ FIXED: Was missing completely, leading to dropped/blank items
                item.subtitle = item.description[:100] if item.description else ''
                combined_results.append(item)

        # =========================================================
        # 5. SHOPS FILTERING
        # =========================================================
        if target_type in ['all', 'shop']:
            shops = Shop.objects.filter(status='approved', is_active=True)
            if query:
                shops = shops.filter(Q(name__icontains=query) | Q(description__icontains=query))
            if district: 
                shops = shops.filter(district__iexact=district)
            if category and category.lower() != 'all':
                shops = shops.filter(category__icontains=category)

            for item in shops:
                item.result_type = 'shop'
                item.title = item.name
                item.subtitle = item.description[:100] if item.description else ''
                item.price = None
                combined_results.append(item)

        # --- Pagination Execution ---
        paginator = UnifiedSearchPagination()
        page = paginator.paginate_queryset(combined_results, request, view=self)
        
        if page is not None:
            serializer = UnifiedSearchItemSerializer(page, many=True, context={'request': request})
            return paginator.get_paginated_response(serializer.data)

        serializer = UnifiedSearchItemSerializer(combined_results, many=True, context={'request': request})
        return Response({
            'next': None,
            'previous': None,
            'count': len(combined_results),
            'results': serializer.data
        })