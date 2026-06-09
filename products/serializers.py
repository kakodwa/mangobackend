from rest_framework import serializers
from mangohub.serializers import ReviewSerializer
from .models import Product, ProductImage, ProductReview,Banner,AppVersion,Favorite


class FavoriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Favorite
        fields = '__all__'

class AppVersionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppVersion
        fields = '__all__'

class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['id', 'image', 'alt_text', 'cta_text', 'is_primary']


class ProductSerializer(serializers.ModelSerializer):
    images = serializers.SerializerMethodField()
    shop_name = serializers.CharField(source='shop.name', read_only=True)
    owner_id = serializers.IntegerField(source='shop.owner.id', read_only=True)
    shop_district = serializers.CharField(source='shop.district',read_only=True,)
    reviews = ReviewSerializer(many=True)
    shop_phone_number = serializers.CharField(
        source='shop.phone_number',
        read_only=True
    )


    class Meta:
        model = Product
        fields = [
            'id', 'shop', 'shop_name', 'name', 'slug',
            'description', 'image', 'category','shop_district',
            'price', 'original_price', 'discount_percentage',
            'stock', 'sku', 'is_active','shop_phone_number',
            'rating', 'total_reviews',
            'images', 'created_at','owner_id','reviews'
        ]
        read_only_fields = ['id', 'shop', 'created_at']

    def get_images(self, obj):
        request = self.context.get('request')

        images = []
        for img in obj.images.all():
            if request:
                images.append(request.build_absolute_uri(img.image.url))
            else:
                images.append(img.image.url)
        return images


class ProductCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = [
            'id',  # ✅ include id (read-only safety)
            'name',
            'description',
            'image',
            'category',
            'price',
            'original_price',
            'discount_percentage',
            'stock',
            'is_active',
        ]
        read_only_fields = ['id']

    def create(self, validated_data):
        user = self.context['request'].user
        shop = user.shops.first()

        if not shop:
            raise serializers.ValidationError("User has no shop assigned")

        validated_data['shop'] = shop
        return super().create(validated_data)


class ProductReviewSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.get_full_name', read_only=True)

    class Meta:
        model = ProductReview
        fields = ['id', 'product', 'customer_name', 'rating', 'comment', 'created_at']
        read_only_fields = ['id', 'customer', 'created_at']

    def create(self, validated_data):
        validated_data['customer'] = self.context['request'].user
        return super().create(validated_data)


# serializers.py
class BannerSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Banner
        fields = [
            'id',
            'title',
            'subtitle',
            'image_url',
            'url',
        ]

    def get_image_url(self, obj):

        request = self.context.get('request')

        if obj.image:
            return request.build_absolute_uri(
                obj.image.url
            )

        return None