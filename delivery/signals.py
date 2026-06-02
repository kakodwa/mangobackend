from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Delivery
from .delivery_settlement import DeliverySettlementService


@receiver(post_save, sender=Delivery)
def release_escrow_on_delivery(sender, instance, created, **kwargs):

    if created:
        return

    if instance.status != "delivered":
        return

    if instance.escrow_released:
        return

    try:
        DeliverySettlementService.complete_delivery(instance)

        Delivery.objects.filter(id=instance.id).update(
            escrow_released=True
        )

    except Exception as e:
        import logging
        logging.exception("Escrow release failed: %s", e)