from realestate.models import Property

def get_properties():
    return Property.objects.filter(is_publicly_visible=False).order_by('-id')