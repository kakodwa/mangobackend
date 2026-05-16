from rest_framework import serializers
from django.contrib.auth.hashers import make_password
from .models import User, Address

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'phone_number', 
                 'user_type', 'profile_picture', 'bio', 'is_verified', 'date_joined']
        read_only_fields = ['id', 'date_joined']


class UserDetailSerializer(serializers.ModelSerializer):
    address = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'phone_number', 
                 'user_type', 'profile_picture', 'bio', 'is_verified', 'address', 'date_joined']
        read_only_fields = ['id', 'date_joined']

    def get_address(self, obj):
        try:
            address = obj.address
            return AddressSerializer(address).data
        except Address.DoesNotExist:
            return None


class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = [
            'username',
            'email',
            'first_name',
            'last_name',
            'phone_number',
            'user_type',
            'password',
        ]

    def create(self, validated_data):
        return User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            phone_number=validated_data.get('phone_number', ''),
            user_type=validated_data.get('user_type', 'customer'),
        )

class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = ['id', 'street_address', 'city', 'district', 'postal_code', 
                 'latitude', 'longitude', 'is_default']
        read_only_fields = ['id']
