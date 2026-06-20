from rest_framework import serializers


class ProductSerializer(serializers.Serializer):
    pid = serializers.CharField()
    productName = serializers.CharField()
    sellPrice = serializers.CharField()