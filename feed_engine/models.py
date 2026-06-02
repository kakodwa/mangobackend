from django.db import models
from django.contrib.auth import get_user_model

class FeedItem(models.Model):
    TYPE_CHOICES = [
        ("product", "Product"),
        ("shop", "Shop"),
        ("event", "Event"),
        ("lodge", "Lodge"),
        ("property", "Property"),
    ]

    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    object_id = models.PositiveIntegerField()
    score = models.FloatField(default=1.0)
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-score", "-created_at"]




User = get_user_model()


class UserInteraction(models.Model):

    INTERACTION_TYPES = [
        ("view", "View"),
        ("click", "Click"),
        ("like", "Like"),
        ("purchase", "Purchase"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content_type = models.CharField(max_length=20)  # product/shop/event/lodge/property
    object_id = models.PositiveIntegerField()

    interaction_type = models.CharField(max_length=20, choices=INTERACTION_TYPES)

    created_at = models.DateTimeField(auto_now_add=True)