# views.py (Django Backend)
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import render
from hospitality.models import Lodge
from events.models import Event
from products.models import Product
from realestate.models import Property
from shops.models import Shop

from rest_framework import viewsets, permissions
from .models import Review
from .serializers import ReviewSerializer

def get_meta_from_url(request, full_path, path_token, model_class, title_field='name', desc_field='description', image_field='image', price_field=None, currency_field=None):
    """
    Reusable helper to safely parse an item ID from a web deep link path,
    query its database model, and extract its sharing values with optional price tags.
    """
    if path_token in full_path:
        try:
            # 🌟 Extract the integer ID cleanly from your path token strings split array
            item_id = int(full_path.split(path_token)[1].split("/")[0])
            item = model_class.objects.get(id=item_id)
            
            title = getattr(item, title_field, "")
            desc = getattr(item, desc_field, "")
            
            # Dynamic Price Injector Configuration
            if price_field and hasattr(item, price_field):
                raw_price = getattr(item, price_field)
                currency = getattr(item, currency_field, "MWK") if currency_field else "MWK"
                if raw_price:
                    title = f"{title} - {currency} {raw_price:,.0f}"

            # Resolve the image URL cleanly depending on FileField/ImageField setup
            img_attr = getattr(item, image_field, None)
            img_url = ""
            if img_attr and hasattr(img_attr, 'url'):
                img_url = request.build_absolute_uri(img_attr.url)
            elif isinstance(img_attr, str):
                img_url = img_attr

            return {
                "share_title": f"{title} | MangoHub",
                "share_desc": desc[:150] if desc else "Explore listings on MangoHub.",
                "share_image": img_url if img_url else None
            }
        except (ValueError, IndexError, model_class.DoesNotExist):
            pass 
            
    return None


def serve_flutter_web_app(request):
    # Establish strict domain fallbacks
    context = {
        "share_title": "MangoHub Marketplace",
        "share_desc": "Explore products, shops, lodges, events, and properties.",
        "share_image": "https://yourdomain.com/static/icons/Icon-512.png"
    }
    
    full_path = request.path 
    meta_data = None

    # 🏢 SHOPS ROUTING
    if "/shop/" in full_path:
        meta_data = get_meta_from_url(
            request, full_path, "/shop/", Shop, 
            title_field='name', desc_field='description', image_field='logo'
        )

    # 🛍️ PRODUCTS ROUTING
    elif "/product/" in full_path:
        meta_data = get_meta_from_url(
            request, full_path, "/product/", Product, 
            title_field='name', desc_field='description', image_field='image',
            price_field='price'
        )

    # 🎟️ EVENTS ROUTING
    elif "/event/" in full_path:
        meta_data = get_meta_from_url(
            request, full_path, "/event/", Event, 
            title_field='title', desc_field='description', image_field='banner'
        )

    # 🏠 PROPERTIES ROUTING
    elif "/property/" in full_path:
        meta_data = get_meta_from_url(
            request, full_path, "/property/", Property, 
            title_field='title', desc_field='description', image_field='image',
            price_field='price', currency_field='currency'
        )

    # 🏨 LODGES ROUTING
    elif "/lodge/" in full_path:
        meta_data = get_meta_from_url(
            request, full_path, "/lodge/", Lodge, 
            title_field='name', desc_field='description', image_field='image'
        )

    if meta_data:
        context.update({k: v for k, v in meta_data.items() if v is not None})

    return render(request, "index.html", context)




class ReviewViewSet(viewsets.ModelViewSet):
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        queryset = Review.objects.all()
        target_type = self.request.query_params.get('content_type')
        target_id = self.request.query_params.get('object_id')

        if target_type and target_id:
            try:
                content_type = ContentType.objects.get(model=target_type.lower())
                queryset = queryset.filter(content_type=content_type, object_id=target_id)
            except ContentType.DoesNotExist:
                return Review.objects.none()

        return queryset

    # 🛠️ THE FIX: Pass the user explicitly into the save handler
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)