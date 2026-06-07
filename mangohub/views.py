# views.py
from django.shortcuts import render
from hospitality.models import Lodge
from events.models import Event
from products.models import Product
from realestate.models import Property
from shops.models import Shop

def get_meta_from_url(request, full_path, path_token, model_class, title_field='name', desc_field='description', image_field='image', price_field=None, currency_field=None):
    """
    Reusable helper to safely parse an item ID from a web deep link hash fragment,
    query its database model, and extract its sharing values with optional price tags.
    """
    if path_token in full_path:
        try:
            # 1. Parse out the integer ID after the specified string token (e.g., "#/shop/")
            item_id = int(full_path.split(path_token)[1].split("/")[0])
            item = model_class.objects.get(id=item_id)
            
            # 2. Extract basic text attributes dynamically
            title = getattr(item, title_field, "")
            desc = getattr(item, desc_field, "")
            
            # 3. Handle dynamic pricing presentation in link previews if fields exist
            if price_field and hasattr(item, price_field):
                raw_price = getattr(item, price_field)
                # Read specific model currency field (like Property) or default to MWK (like Product)
                currency = getattr(item, currency_field, "MWK") if currency_field else "MWK"
                if raw_price:
                    # Formats price cleanly with commas (e.g., MWK 75,000)
                    title = f"{title} - {currency} {raw_price:,.0f}"

            # 4. Resolve the image URL cleanly depending on FileField/ImageField setup
            img_attr = getattr(item, image_field, None)
            img_url = ""
            if img_attr and hasattr(img_attr, 'url'):
                img_url = request.build_absolute_uri(img_attr.url)
            elif isinstance(img_attr, str):
                img_url = img_attr

            return {
                "share_title": f"{title} | MangoHub",
                "share_desc": desc[:150] if desc else "Explore listings on MangoHub.",
                "share_image": img_url if img_url else None
            }
        except (ValueError, IndexError, model_class.DoesNotExist):
            pass # Gracefully fall back if something goes wrong or item isn't found
            
    return None


def serve_flutter_web_app(request):
    # Establish default fallback context parameters
    context = {
        "share_title": "MangoHub Marketplace",
        "share_desc": "Explore products, shops, lodges, events, and properties.",
        "share_image": "https://yourdomain.com/static/icons/Icon-512.png"
    }
    
    full_path = request.get_full_path()
    meta_data = None

    # 🏢 SHOPS ROUTING
    if "#/shop/" in full_path:
        meta_data = get_meta_from_url(
            request, full_path, "#/shop/", Shop, 
            title_field='name', desc_field='description', image_field='banner'
        )

    # 🛍️ PRODUCTS ROUTING
    elif "#/product/" in full_path:
        meta_data = get_meta_from_url(
            request, full_path, "#/product/", Product, 
            title_field='name', desc_field='description', image_field='image',
            price_field='price' # Maps to standard 'MWK' fallback
        )

    # 🎟️ EVENTS ROUTING
    elif "#/event/" in full_path:
        meta_data = get_meta_from_url(
            request, full_path, "#/event/", Event, 
            title_field='title', desc_field='description', image_field='banner'
        )

    # 🏠 PROPERTIES ROUTING
    elif "#/property/" in full_path:
        meta_data = get_meta_from_url(
            request, full_path, "#/property/", Property, 
            title_field='title', desc_field='description', image_field='image',
            price_field='price', currency_field='currency' # Pulls dynamic currency field from model schema
        )

    # 🏨 LODGES ROUTING
    elif "#/lodge/" in full_path:
        meta_data = get_meta_from_url(
            request, full_path, "#/lodge/", Lodge, 
            title_field='name', desc_field='description', image_field='image'
        )

    # If any specific model data was successfully found, override the fallback context properties
    if meta_data:
        # Update only keys that successfully returned a valid value
        context.update({k: v for k, v in meta_data.items() if v is not None})

    return render(request, "index.html", context)