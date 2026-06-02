from payments.models import EscrowWallet

class EscrowService:

    @staticmethod
    def hold(
        payment,
        beneficiary,
        escrow_type,
        amount,
        commission_rate
    ):

        escrow, created = EscrowWallet.objects.get_or_create(
            payment=payment,
            beneficiary=beneficiary,
            escrow_type=escrow_type,
            defaults={
                "amount": amount,
                "commission_rate": commission_rate,
                "status": "held"
            }
        )

        if not created:
            escrow.amount = amount
            escrow.commission_rate = commission_rate
            escrow.status = "held"
            escrow.save()

        return escrow