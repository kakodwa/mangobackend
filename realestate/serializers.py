from rest_framework import serializers
from .models import Property, PropertyImage, PropertyUnlock
from rest_framework import serializers
from .models import Property, PropertyImage
import decimal
from users.models import User


class PropertyImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = PropertyImage
        fields = ['id', 'image', 'alt_text', 'is_primary']


class PropertySerializer(serializers.ModelSerializer):
    images = PropertyImageSerializer(many=True, read_only=True)
    owner_name = serializers.CharField(source='owner.get_full_name', read_only=True)
    owner_id = serializers.ReadOnlyField(source='owner.id')
    is_unlocked = serializers.SerializerMethodField()

    class Meta:
        model = Property
        fields = [
            'id', 'title', 'slug', 'description', 'property_type', 'status',
            'latitude', 'longitude', 'address', 'city', 'district',
            'bedrooms', 'bathrooms', 'size_sqm', 'price', 'currency',
            'is_publicly_visible', 'unlock_fee', 'view_count','listing_purpose',
            'images', 'owner_id','owner_name', 'is_unlocked', 'created_at'
        ]
        read_only_fields = ['slug', 'view_count', 'created_at']

    def get_is_unlocked(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        try:
            PropertyUnlock.objects.get(property=obj, customer=request.user,is_unlocked=True)
            return True
        except PropertyUnlock.DoesNotExist:
            return False



class PropertyCreateUpdateSerializer(serializers.ModelSerializer):
    images = serializers.ListField(
        child=serializers.ImageField(),
        write_only=True,
        required=False
    )

    class Meta:
        model = Property
        fields = [
            'title',
            'description',
            'property_type',
            'status',
            'latitude',
            'longitude',
            'address',
            'listing_purpose',
            'city',
            'district',
            'bedrooms',
            'bathrooms',
            'size_sqm',
            'price',
            'is_publicly_visible',
            'images',
        ]

    def create(self, validated_data):


        validated_data['latitude'] = round(float(validated_data['latitude']), 7)
        validated_data['longitude'] = round(float(validated_data['longitude']), 7)

        validated_data['owner'] = self.context['request'].user
        images = validated_data.pop('images', [])

        property_obj = Property.objects.create(**validated_data)

        for index, image in enumerate(images):
            PropertyImage.objects.create(
                property=property_obj,
                image=image,
                is_primary=index == 0,
                )

        return property_obj

    def update(self, instance, validated_data):
        images = validated_data.pop('images', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()

        # Optional: replace images
        if images is not None:
            instance.images.all().delete()

            for index, image in enumerate(images):
                PropertyImage.objects.create(
                    property=instance,
                    image=image,
                    is_primary=index == 0,
                )

        return instance


class PropertyUnlockSerializer(serializers.ModelSerializer):
    property_title = serializers.CharField(source='property.title', read_only=True)

    class Meta:
        model = PropertyUnlock
        fields = ['id', 'property', 'property_title', 'unlock_fee', 'unlocked_at']
        read_only_fields = ['unlocked_at']
