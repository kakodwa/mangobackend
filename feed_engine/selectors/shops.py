from shops.models import Shop


def get_shops():
    return Shop.objects.all()


def get_featured():
    return Shop.objects.order_by("-rating")