from wallet.models import WalletTransaction


def get_wallet_analytics(user):
    txns = WalletTransaction.objects.filter(wallet__user=user)

    return {
        "total_transactions": txns.count(),
        "credits": txns.filter(transaction_type="credit").count(),
        "debits": txns.filter(transaction_type="debit").count(),
    }