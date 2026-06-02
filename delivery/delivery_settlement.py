from payments.models import EscrowWallet
from payments.services.settlement_service import SettlementService


class DeliverySettlementService:

    @staticmethod
    def complete_delivery(delivery):

        # avoid double execution (per request lifecycle)
        if getattr(delivery, "_escrow_released", False):
            return

        try:
            escrow = EscrowWallet.objects.filter(
                payment__order=delivery.order,
                beneficiary=delivery.seller,
                escrow_type="order",
                status="held"
                ).first()

            if not escrow:
                return

        except EscrowWallet.DoesNotExist:
            return

        # release through unified system
        SettlementService.release(escrow)

        delivery._escrow_released = True