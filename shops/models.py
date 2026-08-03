from io import BytesIO
import qrcode
from email.mime.image import MIMEImage

from django.conf import settings
from django.core.files import File
from django.db import models
from django.utils.text import slugify
from django.contrib.contenttypes.fields import GenericRelation
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

from users.models import User
from mangohub.models import Review


class Shop(models.Model):
    SHOP_STATUS_CHOICES = (
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('suspended', 'Suspended'),
    )

    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shops'
    )

    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(unique=True)

    description = models.TextField()

    logo = models.ImageField(upload_to='shop_logos/')
    banner = models.ImageField(
        upload_to='shop_banners/',
        blank=True,
        null=True
    )

    category = models.CharField(max_length=100)

    # QR
    qr_code = models.ImageField(
        upload_to="shop_qr/",
        blank=True,
        null=True,
    )

    qr_scan_count = models.PositiveIntegerField(default=0)

    # Location
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    district = models.CharField(max_length=100)

    # Contact
    phone_number = models.CharField(max_length=20)
    email = models.EmailField()

    # Status
    status = models.CharField(
        max_length=20,
        choices=SHOP_STATUS_CHOICES,
        default='pending'
    )

    is_active = models.BooleanField(default=True)

    # Reviews
    reviews = GenericRelation(Review)
    rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=0
    )
    total_reviews = models.IntegerField(default=0)

    # Dates
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def generate_qr(self):
        """Generates public tracking QR code for shop."""
        backend_domain = "https://malatrade.com" 
        qr_url = f"{backend_domain}/qr/shop/{self.id}/"

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_url)
        qr.make(fit=True)

        image = qr.make_image(fill_color="#000000", back_color="#FFFFFF")

        buffer = BytesIO()
        image.save(buffer, format="PNG")
        buffer.seek(0)
        
        filename = f"shop_{self.id}.png"
        self.qr_code.save(filename, File(buffer), save=False)

    def send_approval_email(self):
        """Renders HTML template & sends email with attached inline QR code."""
        recipient = self.email or self.owner.email
        owner_name = self.owner.get_full_name() or self.owner.username
        subject = f"Your Shop '{self.name}' is Approved on MalaTrade!"
        shop_url = f"https://malatrade.com/shop/{self.id}"

        has_qr = bool(self.qr_code)

        context = {
            'owner_name': owner_name,
            'shop_name': self.name,
            'shop_url': shop_url,
            'has_qr': has_qr,
        }

        # Render HTML and plain-text templates
        text_content = render_to_string('emails/shop_approved.txt', context)
        html_content = render_to_string('emails/shop_approved.html', context)

        # Send via settings.DEFAULT_FROM_EMAIL ("MalaTrade Support <support@malatrade.com>")
        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[recipient]
        )
        msg.attach_alternative(html_content, "text/html")

        # Attach QR Code Image as Inline CID
        if has_qr:
            try:
                with self.qr_code.open('rb') as f:
                    mime_image = MIMEImage(f.read())
                    mime_image.add_header('Content-ID', '<shop_qr_code>')
                    mime_image.add_header('Content-Disposition', 'inline', filename=f"shop_{self.id}_qr.png")
                    msg.attach(mime_image)
            except Exception:
                pass  # Fallback gracefully if storage read fails

        msg.send(fail_silently=False)

    def save(self, *args, **kwargs):
        # 1. Generate unique slug
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            Klass = self.__class__
            while Klass.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug

        # 2. Track status update to 'approved'
        status_changed_to_approved = False
        if self.pk:
            old_instance = Shop.objects.filter(pk=self.pk).only('status').first()
            if old_instance and old_instance.status != 'approved' and self.status == 'approved':
                status_changed_to_approved = True

        is_new = self.pk is None

        # 3. Save regular data
        super().save(*args, **kwargs)

        # 4. Generate QR code on creation
        if is_new and not self.qr_code:
            self.generate_qr()
            super().save(update_fields=["qr_code"])

        # 5. Send approval email with QR code inline attachment
        if status_changed_to_approved:
            if not self.qr_code:
                self.generate_qr()
                super().save(update_fields=["qr_code"])
            self.send_approval_email()


class ShopReview(models.Model):
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name='reviews')
    customer = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'user_type': 'customer'})
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('shop', 'customer')

    def __str__(self):
        return f"{self.shop.name} - {self.rating}★"