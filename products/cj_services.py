import time
import requests
from django.conf import settings
from django.core.files.base import ContentFile
from decimal import Decimal
from .models import Product, ProductImage, ProductVariant
from shops.models import Shop

class CJService:
    # Use the endpoint domain from your curl request
    BASE_URL = "https://developers.cjdropshipping.com"
    
    # Store your full string ("CJUserNum@api@xxxx...") in this environment variable
    CJ_API_KEY = settings.CJ_APP_KEY 

    def __init__(self):
        self.session = requests.Session()
        self._token = None
        self._token_expires_at = 0

    def get_token(self):
        """Fetches and caches the token using the new apiKey format."""
        current_time = time.time()
        
        # Check if the token is still fresh (giving it a 5-minute safety buffer)
        if self._token and current_time < (self._token_expires_at - 300):
            return self._token

        url = f"{self.BASE_URL}/api2.0/v1/authentication/getAccessToken"
        
        # Match your exact curl request payload
        payload = {
            "apiKey": self.CJ_API_KEY  # Note the exact key name: 'apiKey'
        }

        try:
            response = self.session.post(url, json=payload, timeout=10)
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as e:
            raise Exception(f"Failed to connect to CJ API: {e}")

        # If CJ sends back result: false or code != 200
        if not data.get("result") and data.get("code") != 200:
            raise Exception(f"CJ API Error: {data.get('message', 'Unknown Error')}")

        # Extract the token from the data payload
        token_data = data.get("data", {})
        self._token = token_data.get("accessToken")
        
        if not self._token:
            raise Exception(f"CJ API Response missing accessToken: {data}")

        # The new token lasts 180 days, but let's safely parse or fallback
        # (180 days = 15,552,000 seconds)
        self._token_expires_at = current_time + 15552000

        return self._token

    def get_headers(self):
        return {
            "CJ-Access-Token": self.get_token(),
            "Content-Type": "application/json"
        }

    def get_products(self, page=2, page_size=20):
        """
        Fetches products from CJ Dropshipping using the correct parameters.
        Forces the search term index exclusively to shoes for Mangogub.
        """
        # Endpoint tracking path 
        url = f"{self.BASE_URL}/api2.0/v1/product/listV2"
        
        # FIXED: Use 'page', 'size', and 'keyWord' matching the V2 specifications
        params = {
            "page": page,
            "size": page_size,
            "keyWord": "Nike shoes"  # Explicitly matches the working curl test variable logic
        }
        
        try:
            response = self.session.get(
                url,
                headers=self.get_headers(),
                params=params,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {"success": False, "error": str(e)}


    def product_detail(self, pid):
        url = f"{self.BASE_URL}/api2.0/v1/product/query"
        try:
            response = self.session.get(url, headers=self.get_headers(), params={"pid": pid}, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {"success": False, "error": str(e)}

    '''def sync_cj_shoe_to_mangogub(self, cj_product_id, target_shop_id):
        """
        Maps CJ Footwear data fields straight into your current custom Product model layout.
        """
        detail_data = self.product_detail(cj_product_id)
        if not detail_data.get("result") or detail_data.get("code") != 200:
            return False
            
        product_info = detail_data.get("data", {})
        try:
            shop = Shop.objects.get(id=target_shop_id)
        except Shop.DoesNotExist:
            raise Exception(f"Shop with ID {target_shop_id} does not exist.")

        # Extract base default pricing metrics
        variants = product_info.get("variants", [])
        if not variants:
            return False
            
        # Get baseline wholesale cost from first variant array node
        base_wholesale = Decimal(str(variants[0].get("variantPrice", "0.00")))
        
        # Apply 2.5x Retail Markup strategy to guarantee $0 capital safety margin
        calculated_retail_price = base_wholesale * Decimal("2.5")
        calculated_original_price = calculated_retail_price * Decimal("1.2") # Visual anchor markup discount

        # 1. Save straight into your existing core Product model
        # Using a custom sku structure pattern 'CJ-PID' to keep clean records
        product, created = Product.objects.update_or_create(
            sku=f"CJ-{product_info.get('pid')}",
            defaults={
                "shop": shop,
                "name": product_info.get("productNameEn"),
                "description": product_info.get("description", "No description provided."),
                "category": "Shoes", # Force footwear categorization layout
                "price": calculated_retail_price,
                "original_price": calculated_original_price,
                "discount_percentage": 20,
                "stock": sum(int(v.get("variantStandardQuantity", 0)) for v in variants),
                "is_active": True,
            }
        )

        # Download and pass image file binary directly into your ImageField to trigger your compression utility pipeline
        if created and product_info.get("productImage"):
            try:
                img_res = requests.get(product_info.get("productImage"), timeout=15)
                if img_res.status_code == 200:
                    img_name = f"cj_{product_info.get('pid')}.jpg"
                    product.image.save(img_name, ContentFile(img_res.content), save=True)
            except Exception:
                pass # Fallback safely if image retrieval hits structural network blocks

        # 2. Map Secondary Gallery Images to your existing ProductImage model
        gallery_images = product_info.get("productImageList", [])
        for idx, img_url in enumerate(gallery_images[:4]): # Keep the first 4 gallery items to balance database size
            try:
                gallery_res = requests.get(img_url, timeout=15)
                if gallery_res.status_code == 200:
                    p_img = ProductImage(product=product, alt_text=f"{product.name} View {idx+1}", is_primary=False)
                    p_img.image.save(f"gallery_{product.id}_{idx}.jpg", ContentFile(gallery_res.content), save=True)
            except Exception:
                pass

        # 3. Create structural records in your new ShoeVariant size chart matrix
        for variant in variants:
            cj_size_value = variant.get("variantKey", "") 
            extracted_eu_size = "".join(filter(str.isdigit, cj_size_value))
            
            # Extract color cleanly
            color_name = "Default"
            if "-" in cj_size_value:
                parts = cj_size_value.split("-")
                color_name = parts[0] if not parts[0].isdigit() else "Standard"

            ProductVariant.objects.update_or_create(
                cj_variant_id=variant.get("vid"),
                defaults={
                    "product": product,
                    "sku": variant.get("variantSku"),
                    "color": color_name,
                    "size_eu": int(extracted_eu_size) if extracted_eu_size else None,
                    "wholesale_price": Decimal(str(variant.get("variantPrice", "0.00"))),
                    "weight_g": variant.get("variantWeight", 0),
                    "stock": int(variant.get("variantStandardQuantity", 0)),
                }
            )
        return True'''
