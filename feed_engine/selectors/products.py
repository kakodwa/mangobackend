import random
from products.models import Product


def get_products():
    return Product.objects.all()


def get_trending():
    return Product.objects.order_by("-total_reviews")[:20]


def get_random_category_products(limit=10):
    # 1. Get all unique categories that currently have active products
    categories = Product.objects.filter(is_active=True).values_list('category', flat=True).distinct()
    
    if not categories:
        return {"category": None, "products": []}
    
    # 2. Select one category randomly
    random_category = random.choice(list(categories))
    
    # 3. Query products under that category
    products = Product.objects.filter(
        category=random_category, 
        is_active=True
    ).order_by("-created_at")[:limit]
    
    return {
        "category": random_category,
        "products": products
    }