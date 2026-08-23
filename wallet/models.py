from django.db import models
from users.models import User
from decimal import Decimal
from payments.models import EscrowWallet


class CompanyWallet(models.Model):
    name = models.CharField(max_length=100, default="Main Company Wallet")

    # 1. NET PLATFORM PROFIT (Your touchable earnings)
    balance = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Net company profit available after reserving payout fees"
    )

    # 2. UNIFIED PAYOUT BUFFER (Reserves 2% + MWK 700 per sale for vendor cashouts)
    vault_processing_buffer = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Reserved pool to cover PayChangu payout transaction fees"
    )

    # 3. GROSS COMMISSIONS COLLECTED (Total revenue captured before split)
    total_earnings = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Gross commission earnings collected across all sales"
    )

    # 4. ACTUAL FEES PAID TO PAYCHANGU (Audit log of payout fees charged)
    total_gateway_fees_paid = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Total payout processing fees charged by PayChangu"
    )

    updated_at = models.DateTimeField(auto_now=True)

    def credit_commission(self, gross_commission_amount, percentage=Decimal("2.00"), fixed_fee=Decimal("700.00")):
        """
        Splits gross transaction commission into:
        1. Unified Reserve Buffer = (Gross * 2%) + MWK 700
        2. Net Company Profit = Gross - Buffer
        """
        gross = Decimal(str(gross_commission_amount))
        
        # Calculate unified reserve: 2% of commission + MWK 700
        payout_reserve = (gross * (percentage / Decimal("100"))) + fixed_fee
        
        # If gross commission is smaller than MWK 700, prevent negative profit
        payout_reserve = min(payout_reserve, gross)
        net_profit = gross - payout_reserve

        self.total_earnings += gross
        self.vault_processing_buffer += payout_reserve
        self.balance += net_profit

        self.save(update_fields=[
            'balance', 
            'vault_processing_buffer', 
            'total_earnings', 
            'updated_at'
        ])

    def record_payout_gateway_fee(self, fee_amount):
        """
        Deducts PayChangu's actual payout charge from the reserved buffer.
        """
        fee = Decimal(str(fee_amount))
        self.vault_processing_buffer -= fee
        self.total_gateway_fees_paid += fee
        self.save(update_fields=[
            'vault_processing_buffer', 
            'total_gateway_fees_paid', 
            'updated_at'
        ])

    def __str__(self):
        return (
            f"{self.name} | Net Profit: MWK {self.balance} | "
            f"Payout Buffer: MWK {self.vault_processing_buffer} | "
            f"Gross Earned: MWK {self.total_earnings}"
        )



class Wallet(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='wallet')
    balance = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    currency = models.CharField(max_length=3, default='MWK')
    total_earnings = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_withdrawn = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    transaction_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def escrow_balance(self):
        """
        Calculates total net escrow funds currently 'held' for this seller.
        Subtracts the escrow commission rate from held amounts.
        """
        
        held_escrows = EscrowWallet.objects.filter(
            beneficiary=self.user,
            status='held'
        )
        
        total_escrow = Decimal("0.00")
        for escrow in held_escrows:
            if escrow.amount:
                rate = escrow.commission_rate or Decimal("0.00")
                commission = (escrow.amount * rate) / Decimal("100")
                net_amount = escrow.amount - commission
                total_escrow += net_amount
                
        return total_escrow

    def __str__(self):
        return f"Wallet - {self.user.username} (Balance: {self.balance} | Escrow: {self.escrow_balance})"



class CompanyWalletTransaction(models.Model):

    TRANSACTION_TYPES = (
        ("credit", "Credit"),
        ("debit", "Debit"),
    )

    SOURCES = (
        ("order_commission", "Order Commission"),
        ("property_unlock_commission", "Property Unlock Commission"),
    )

    wallet = models.ForeignKey(
        CompanyWallet,
        on_delete=models.CASCADE,
        related_name="transactions"
    )

    transaction_type = models.CharField(
        max_length=20,
        choices=TRANSACTION_TYPES
    )

    source = models.CharField(
        max_length=50,
        choices=SOURCES
    )

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    # 🔥 COMMISSION RATE
    transaction_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00,
        help_text="Commission percentage used"
    )

    balance_before = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    balance_after = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    reference = models.CharField(
        max_length=200,
        blank=True,
        null=True
    )

    description = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.source} - {self.amount}"


class WalletTransaction(models.Model):
    TRANSACTION_TYPE_CHOICES = (
        ('credit', 'Credit'),
        ('debit', 'Debit'),
    )

    SOURCE_CHOICES = (
        ('order_payment', 'Order Payment'),
        ('property_unlock', 'Property Unlock Payment'),
        ('withdrawal', 'Withdrawal'),
        ('refund', 'Refund'),
        ('bonus', 'Bonus'),
    )

    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPE_CHOICES)
    source = models.CharField(max_length=30, choices=SOURCE_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    balance_before = models.DecimalField(max_digits=15, decimal_places=2)
    balance_after = models.DecimalField(max_digits=15, decimal_places=2)
    reference = models.CharField(max_length=255, blank=True)
    transaction_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00,
        help_text="Commission percentage used"
    )
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.transaction_type.upper()} - {self.amount}"


# models.py
from django.db import models
from users.models import User

class Withdrawal(models.Model):
    WITHDRAWAL_STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('processed', 'Processed'),
        ('rejected', 'Rejected'),
    )

    PAYOUT_METHODS = (
        ('mobile_money', 'Mobile Money'),
        ('bank_transfer', 'Bank Transfer'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='withdrawals')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=WITHDRAWAL_STATUS_CHOICES, default='pending')
    payout_method = models.CharField(max_length=20, choices=PAYOUT_METHODS, default='mobile_money')
    
    # Flexible fields depending on payout_method
    account_holder_name = models.CharField(max_length=255)
    account_number = models.CharField(max_length=50, help_text="Bank Account or Mobile Number")
    
    # Bank Only Fields (Optional if mobile_money)
    bank_name = models.CharField(max_length=255, blank=True, null=True)
    bank_uuid = models.CharField(max_length=100, blank=True, null=True, help_text="PayChangu Bank UUID")
    bank_branch = models.CharField(max_length=255, blank=True, null=True)
    
    requested_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)

    class Meta:
        ordering = ['-requested_at']
