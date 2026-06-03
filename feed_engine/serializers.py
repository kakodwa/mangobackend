from rest_framework import serializers
from django.contrib.auth import get_user_model
from hospitality.models import Lodge
from events.models import Event
from products.models import Product
from realestate.models import Property
from shops.models import Shop

User = get_user_model()


# ==========================================
# SUB-SERIALIZERS TO MAP FULL DETAILS PAYLOAD
# ==========================================

class EventDetailSerializer(serializers.ModelSerializer):

    regular_ticket_price = serializers.ReadOnlyField()
    total_tickets = serializers.ReadOnlyField()
    tickets_sold = serializers.ReadOnlyField()
    tickets_remaining = serializers.ReadOnlyField()

    class Meta:
        model = Event
        fields = '__all__'

class LodgeDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lodge
        fields = '__all__'

class ProductDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'

class PropertyDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Property
        fields = '__all__'

class ShopDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shop
        fields = '__all__'

# ==========================================
# MAIN UNIFIED SEARCH SERIALIZER
# ==========================================

class UnifiedSearchItemSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    result_type = serializers.CharField()  # 'event', 'lodge', 'product', 'property', 'shop'
    title = serializers.CharField()       # Unified display title/name
    subtitle = serializers.CharField()    # Secondary text (description snippet)
    image_url = serializers.SerializerMethodField()
    price = serializers.DecimalField(max_digits=15, decimal_places=2, required=False, allow_null=True)
    city = serializers.CharField(required=False, allow_null=True)
    district = serializers.CharField(required=False, allow_null=True)
    
    # Extra payload dynamically taking the fully nested object representation
    details = serializers.SerializerMethodField()

    def get_image_url(self, obj):
        request = self.context.get('request')
        image_field = None
        
        if hasattr(obj, 'banner') and obj.banner:
            image_field = obj.banner
        elif hasattr(obj, 'image') and obj.image:
            image_field = obj.image
        elif hasattr(obj, 'logo') and obj.logo:
            image_field = obj.logo
            
        if image_field:
            return request.build_absolute_uri(image_field.url) if request else image_field.url
        return None

    def get_details(self, obj):
        """
        Detects the object runtime type and passes it down to its 
        respective nested sub-serializer to render all model fields.
        """
        context = self.context
        if isinstance(obj, Product):
            return ProductDetailSerializer(obj, context=context).data
        elif isinstance(obj, Event):
            return EventDetailSerializer(obj, context=context).data
        elif isinstance(obj, Lodge):
            return LodgeDetailSerializer(obj, context=context).data
        elif isinstance(obj, Property):
            return PropertyDetailSerializer(obj, context=context).data
        elif isinstance(obj, Shop):
            return ShopDetailSerializer(obj, context=context).data
        return {}