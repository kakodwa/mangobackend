from rest_framework import serializers
from .models import Shop, ShopReview
from django.utils.text import slugify
from users.serializers import UserSerializer

class ShopSerializer(serializers.ModelSerializer):
    owner = UserSerializer(read_only=True)
    product_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Shop
        fields = ['id', 'owner', 'name', 'slug', 'description', 'logo', 'banner', 
                 'category', 'latitude', 'longitude', 'address', 'city', 'district',
                 'phone_number', 'email', 'status', 'is_active', 'rating', 
                 'total_reviews','product_count', 'created_at','qr_code','qr_scan_count',]
        read_only_fields = ['id', 'owner', 'status', 'created_at']


class ShopCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shop
        fields = ['name', 'description', 'logo', 'banner', 'category',
                 'latitude', 'longitude', 'address', 'city', 'district',
                 'phone_number', 'email']

    def create(self, validated_data):
        validated_data['owner'] = self.context['request'].user
        #validated_data['slug'] = slugify(validated_data['name'])
        return super().create(validated_data)


class ShopReviewSerializer(serializers.ModelSerializer):
    customer = UserSerializer(read_only=True)
    
    class Meta:
        model = ShopReview
        fields = ['id', 'shop', 'customer', 'rating', 'comment', 'created_at']
        read_only_fields = ['id', 'customer', 'created_at']

    def create(self, validated_data):
        validated_data['customer'] = self.context['request'].user
        return super().create(validated_data)
