from rest_framework import serializers
from .models import Lodge, Room, Booking, LodgeImage, Review,Amenity
from decimal import Decimal, ROUND_HALF_UP



class AmenitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Amenity
        fields = ['id', 'name', 'icon']

class LodgeImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = LodgeImage
        fields = '__all__'


class RoomSerializer(serializers.ModelSerializer):
    owner_id = serializers.IntegerField(
        source='lodge.owner.id',
        read_only=True
    )

    owner_username = serializers.CharField(
        source='lodge.owner.username',
        read_only=True
    )
    class Meta:
        model = Room
        fields = '__all__'  
        

class ReviewSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.username', read_only=True)

    class Meta:
        model = Review
        fields = '__all__'  


class LodgeSerializer(serializers.ModelSerializer):

    images = LodgeImageSerializer(many=True, read_only=True)
    rooms = RoomSerializer(many=True, read_only=True)
    reviews = ReviewSerializer(many=True, read_only=True)

    amenities = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Amenity.objects.all(),
        required=False
    )

    owner_id = serializers.IntegerField(
        source='owner.id',
        read_only=True
    )

    class Meta:
        model = Lodge
        fields = '__all__'
        read_only_fields = ['owner']

    def create(self, validated_data):

        request = self.context.get("request")

        images_data = (
            request.FILES.getlist("images")
            if request else []
        )

        amenities = validated_data.pop("amenities", [])

        lodge = Lodge.objects.create(**validated_data)

        # Save uploaded images
        for img in images_data:
            LodgeImage.objects.create(
                lodge=lodge,
                image=img
            )

        # Save amenities
        if amenities:
            lodge.amenities.set(amenities)

        return lodge

    def update(self, instance, validated_data):

        request = self.context.get("request")

        images_data = (
            request.FILES.getlist("images")
            if request else []
        )

        amenities = validated_data.pop("amenities", None)

        # Update normal fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()

        # Update amenities
        if amenities is not None:
            instance.amenities.set(amenities)

        # Optional: add new uploaded images during update
        for img in images_data:
            LodgeImage.objects.create(
                lodge=instance,
                image=img
            )

        return instance

class BookingSerializer(serializers.ModelSerializer):
    lodge_name = serializers.CharField(
        source='lodge.name',
        read_only=True
    )

    room_name = serializers.CharField(
        source='room.title',
        read_only=True
    )

    room_number = serializers.CharField(
        source='room.room_number',
        read_only=True
    )

    qr_code = serializers.ImageField(read_only=True)

    class Meta:
        model = Booking
        fields = [
            'id',
            'booking_reference',
            'check_in_date',
            'check_out_date',
            'booking_status',
            'payment_status',
            'total_amount',
            'total_nights',

            'lodge_name',
            'room_name',
            'room_number',

            'room',
            'lodge',
            'qr_code',
        ]

        read_only_fields = (
            'customer',
            'booking_reference',
            'total_nights',
            'subtotal',
            'total_amount',
            'lodge',
        )

    def create(self, validated_data):
        room = validated_data.get("room")
        validated_data["lodge"] = room.lodge
        return Booking.objects.create(**validated_data)