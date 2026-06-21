from rest_framework import serializers
from mangohub.serializers import ReviewSerializer
from .models import Product, ProductImage, ProductReview,Banner,AppVersion,Favorite,ProductVariant


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



class ProductVariantSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductVariant
        fields = ['id', 'cj_variant_id', 'sku', 'attributes', 'wholesale_price', 'weight_g', 'stock']
        # Do NOT put fields like 'attributes' or 'stock' inside read_only_fields here


class ProductSerializer(serializers.ModelSerializer):
    images = serializers.SerializerMethodField()
    # 1. Nest the ProductVariantSerializer inside the read serializer
    variants = ProductVariantSerializer(many=True, read_only=True) 
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
            'images', 'created_at','owner_id','reviews',
            'variants'
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
    # Accept variants in the write payload
    variants = ProductVariantSerializer(many=True, required=False)

    class Meta:
        model = Product
        fields = [
            'id',
            'name',
            'description',
            'image',
            'category',
            'price',
            'original_price',
            'discount_percentage',
            'stock',
            'is_active',
            'variants', # 👈 Added
        ]
        read_only_fields = ['id']

    def create(self, validated_data):
        user = self.context['request'].user
        shop = user.shops.first()

        if not shop:
            raise serializers.ValidationError("User has no shop assigned")

        validated_data['shop'] = shop
        
        # Pop the variant data out before creating the Product instance
        variants_data = validated_data.pop('variants', [])
        
        # 1. Create the parent product
        product = super().create(validated_data)
        
        # 2. Create the linked variants
        for variant_data in variants_data:
            ProductVariant.objects.create(product=product, **variant_data)
            
        return product


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

