from io import BytesIO
from PIL import Image, ImageDraw, ImageFont  # 👈 Added ImageDraw and ImageFont
from django.core.files.base import ContentFile

def process_and_compress_image(image_field, ratio_type="square", target_width=1000):
    """
    Resizes, labels, and compresses an image that has already been pre-cropped by Flutter.
    ratio_type: 'square' (1:1) or 'landscape' (16:9)
    target_width: The width in pixels to scale the final image to.
    """
    if not image_field:
        return None

    # Open image
    img = Image.open(image_field)
    
    # Convert transparency layers (PNG) to RGB for high-quality JPEG compatibility
    if img.mode in ('RGBA', 'P'):
        img = img.convert('RGB')

    width, height = img.size

    # --- STEP 1: CALCULATE TARGET HEIGHT WITHOUT RE-CROPPING ---
    if ratio_type == "square":
        target_height = target_width
    elif ratio_type == "landscape":
        target_ratio = 16 / 9
        target_height = int(target_width / target_ratio)
    else:
        current_ratio = width / height
        target_height = int(target_width / current_ratio)

    # --- STEP 2: RESIZE TO TARGET DIMENSIONS ---
    img = img.resize((target_width, target_height), Image.Resampling.LANCZOS)

    # --- STEP 3: ADD "MangoHub" LABEL TO BOTTOM LEFT ---
    draw = ImageDraw.Draw(img)
    
    # Choose a font size relative to the target image width (e.g., ~4.5% of the image width)
    font_size = int(target_width * 0.045)
    
    try:
        # Attempts to load a standard system sans-serif font (works on most Linux/Mac/Windows setups)
        # For production Docker/Ubuntu servers, make sure ttf-dejavu or fonts-liberation is installed
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", font_size)
    except IOError:
        try:
            font = ImageFont.truetype("Arial Bold.ttf", font_size)
        except IOError:
            # Safe ultimate fallback if no custom fonts are found on the server OS
            font = ImageFont.load_default()

    label_text = "MangoHub"
    
    # Set padding margins away from the bottom and left edges
    margin_left = int(target_width * 0.04)   # 4% away from the left edge
    margin_bottom = int(target_height * 0.04) # 4% away from the bottom edge
    
    # Using font.getbbox() to dynamically figure out the height of our rendered string
    text_bbox = draw.textbbox((0, 0), label_text, font=font)
    text_height = text_bbox[3] - text_bbox[1]
    
    # Calculate the exact X and Y coordinates for placement
    x = margin_left
    y = target_height - text_height - margin_bottom

    # Draw a soft dark drop-shadow first so the text remains legible on light backgrounds
    shadow_offset = max(1, int(font_size * 0.05)) # Scaled offset based on text size
    draw.text((x + shadow_offset, y + shadow_offset), label_text, font=font, fill=(0, 0, 0, 140))
    
    # Draw the main crisp white text on top of the shadow
    draw.text((x, y), label_text, font=font, fill=(255, 255, 255))

    # --- STEP 4: COMPRESS AND SAVE TO MEMORY ---
    output = BytesIO()
    img.save(
        output, 
        format='JPEG', 
        quality=88,          
        optimize=True,       
        subsampling=0        
    )
    output.seek(0)

    # Rebuild filename with a clean .jpg extension
    filename = f"{image_field.name.split('.')[0]}.jpg"
    
    # Return a Django-compatible file object
    return ContentFile(output.read(), name=filename)