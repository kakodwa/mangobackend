from products.models import Product


def get_products():
    return Product.objects.all()


def get_trending():
    return Product.objects.order_by("-total_reviews")[:20]