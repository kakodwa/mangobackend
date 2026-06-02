class WithdrawalService:

    @staticmethod
    def request_withdrawal(user, amount):

        wallet = Wallet.objects.get(user=user)

        if wallet.balance < amount:
            raise Exception("Insufficient funds")

        wallet.balance -= amount
        wallet.save()

        Withdrawal.objects.create(
            user=user,
            amount=amount,
            status="pending"
        )