from wallet.models import Wallet
from payments.models import EscrowWallet


class RefundService:

    @staticmethod
    def refund_order(order, seller=None):

        escrows = SellerEscrow.objects.filter(order=order)

        if seller:
            escrows = escrows.filter(seller=seller)

        for escrow in escrows:

            if escrow.status != "held":
                continue

            customer_wallet, _ = Wallet.objects.get_or_create(
                user=order.customer
            )

            customer_wallet.balance += escrow.amount
            customer_wallet.save()

            escrow.status = "refunded"
            escrow.save()