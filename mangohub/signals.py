from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db.models import Avg, Sum
from django.contrib.contenttypes.models import ContentType
from decimal import Decimal

# Internal App Imports
from hospitality.models import Lodge
from events.models import Event
from products.models import Product
from realestate.models import Property
from shops.models import Shop
from mangohub.models import Review

def update_target_rating(content_object):
    """
    This function dynamically updates ratings for WHATEVER was reviewed!
    Works instantly for: Lodge, Event, Property, and Product.
    """
    if not content_object:
        return
        
    if hasattr(content_object, 'rating') and hasattr(content_object, 'total_reviews'):
        # 🛠️ THE CRITICAL CACHE FIX: Look up the model table via ContentType directly to drop proxy cache blocks
        obj_content_type = ContentType.objects.get_for_model(content_object)
        
        # Query the global Review table directly using explicit filter parameters
        product_reviews = Review.objects.filter(content_type=obj_content_type, object_id=content_object.id)
        
        total = product_reviews.count()
        average = product_reviews.aggregate(Avg('rating'))['rating__avg'] or 0
        calculated_rating = Decimal(str(round(float(average), 2)))

        # 🕵️‍♂️ Debug Tracker (Keep this to confirm live data modifications inside your console)
        print(f"📊 SYSTEM CALCULATION -> Total Found: {total} | Calculated Avg: {calculated_rating}")
        
        # 🛠️ THE SQL FORCE WRITE FIX: Target the database manager using a direct update loop query execution
        model_class = content_object.__class__
        model_class.objects.filter(id=content_object.id).update(
            rating=calculated_rating,
            total_reviews=total
        )
        
        # Specific business extension: Update parent shop aggregations when handling a Product
        if isinstance(content_object, Product):
            # Fetch a clean version of the shop object to clear structural relationships chains
            fresh_shop = Shop.objects.filter(id=content_object.shop_id).first()
            if fresh_shop:
                update_shop_rating(fresh_shop)


def update_shop_rating(shop):
    """
    Special calculation helper purely for Shops.
    Recalculates a shop's aggregate matrix based on its active products.
    """
    if not shop:
        return
        
    active_products = shop.products.filter(is_active=True)
    
    # Aggregate metrics efficiently from active product items inside a single query block
    metrics = active_products.aggregate(
        total_count=Sum('total_reviews'),
        avg_rating=Avg('rating')
    )
    
    total_reviews = metrics['total_count'] or 0
    avg_rating = metrics['avg_rating'] or 0
        
    # Force write directly into Shop table columns
    Shop.objects.filter(id=shop.id).update(
        rating=Decimal(str(round(float(avg_rating), 2))),
        total_reviews=total_reviews
    )


@receiver(post_save, sender=Review)
def review_saved(sender, instance, **kwargs):
    print(f"🔥 SIGNAL TRIGGERED! New review for: {instance.content_object} (ID: {instance.object_id})")
    update_target_rating(instance.content_object)

@receiver(post_delete, sender=Review)
def review_deleted(sender, instance, **kwargs):
    print(f"🗑️ SIGNAL TRIGGERED! Review dropped for: {instance.content_object} (ID: {instance.object_id})")
    update_target_rating(instance.content_object)