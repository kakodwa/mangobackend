from rest_framework import serializers
from django.contrib.contenttypes.models import ContentType
from .models import Review

class ReviewSerializer(serializers.ModelSerializer):
    entity_type = serializers.SerializerMethodField(read_only=True)
    user_name = serializers.CharField(source='user.username', read_only=True)
    
    # 📥 Accept write-only payloads coming from Flutter's submitReview()
    resource_type = serializers.CharField(write_only=True)
    resource_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Review
        fields = [
            'id', 'user_name', 'rating', 'title', 'comment', 
            'entity_type', 'resource_type', 'resource_id', 'created_at'
        ]

    def get_entity_type(self, obj):
        return obj.content_type.model

    def validate(self, data):
        """
        Intercepts the write-only payload and safely translates it 
        into Django ContentType parameters before database validation.
        """
        resource_type = data.get('resource_type')
        resource_id = data.get('resource_id')

        try:
            # Resolve 'product', 'event', etc., to Django's content type table
            content_type = ContentType.objects.get(model=resource_type.lower().strip())
        except ContentType.DoesNotExist:
            raise serializers.ValidationError({"resource_type": f"Invalid resource type: '{resource_type}'"})

        # Inject the parsed variables back into the validated data dictionary
        data['content_type'] = content_type
        data['object_id'] = resource_id
        return data

    def create(self, validated_data):
        # Remove the extra fields used for tracking payload translations
        resource_type = validated_data.pop('resource_type', None)
        resource_id = validated_data.pop('resource_id', None)
        
        content_type = validated_data.pop('content_type')
        object_id = validated_data.pop('object_id')
        user = self.context['request'].user

        # Create or update the review atomically
        review, created = Review.objects.update_or_create(
            user=user,
            content_type=content_type,
            object_id=object_id,
            defaults={
                'rating': validated_data.get('rating'),
                'title': validated_data.get('title', ''),
                'comment': validated_data.get('comment', ''),
            }
        )
        return review