from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from django.core.files.base import ContentFile


def process_and_compress_image(image_field, ratio_type="square", target_width=1000):
    """
    Resizes, adds a semi-transparent Malatrade watermark,
    and compresses an image.

    ratio_type:
        - "square"     -> 1:1
        - "landscape"  -> 16:9
        - anything else keeps original aspect ratio
    """

    if not image_field:
        return None

    # -----------------------------
    # Open image
    # -----------------------------
    img = Image.open(image_field)

    # Convert to RGBA to support transparency
    if img.mode != "RGBA":
        img = img.convert("RGBA")

    width, height = img.size

    # -----------------------------
    # Calculate target dimensions
    # -----------------------------
    if ratio_type == "square":
        target_height = target_width

    elif ratio_type == "landscape":
        target_height = int(target_width / (16 / 9))

    else:
        target_height = int(target_width / (width / height))

    # -----------------------------
    # Resize
    # -----------------------------
    img = img.resize(
        (target_width, target_height),
        Image.Resampling.LANCZOS
    )

    # -----------------------------
    # Create transparent overlay
    # -----------------------------
    overlay = Image.new("RGBA", img.size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(overlay)

    # -----------------------------
    # Watermark settings
    # -----------------------------
    label_text = "malatrade.com"

    font_size = max(22, int(target_width * 0.045))

    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", font_size)
    except IOError:
        try:
            font = ImageFont.truetype("Arial Bold.ttf", font_size)
        except IOError:
            font = ImageFont.load_default()

    # Padding
    margin_left = int(target_width * 0.04)
    margin_bottom = int(target_height * 0.04)

    # Text size
    bbox = draw.textbbox((0, 0), label_text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    x = margin_left
    y = target_height - text_height - margin_bottom

    # -----------------------------
    # Shadow
    # -----------------------------
    shadow_offset = max(2, int(font_size * 0.06))

    draw.text(
        (x + shadow_offset, y + shadow_offset),
        label_text,
        font=font,
        fill=(0, 0, 0, 60)  # Transparent black shadow
    )

    # -----------------------------
    # Main watermark
    # -----------------------------
    draw.text(
        (x, y),
        label_text,
        font=font,
        fill=(255, 255, 255, 75)  # Semi-transparent white
    )

    # -----------------------------
    # Merge overlay with image
    # -----------------------------
    img = Image.alpha_composite(img, overlay)

    # Convert back to RGB for JPEG
    img = img.convert("RGB")

    # -----------------------------
    # Compress
    # -----------------------------
    output = BytesIO()

    img.save(
        output,
        format="JPEG",
        quality=88,
        optimize=True,
        subsampling=0,
    )

    output.seek(0)

    # -----------------------------
    # Filename
    # -----------------------------
    filename = f"{image_field.name.rsplit('.', 1)[0]}.jpg"

    return ContentFile(output.read(), name=filename)