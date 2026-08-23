import re
from rest_framework import serializers
from .models import Wallet, WalletTransaction, Withdrawal


class WalletSerializer(serializers.ModelSerializer):
    escrow_balance = serializers.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        read_only=True
    )

    class Meta:
        model = Wallet
        fields = [
            'id', 
            'balance', 
            'escrow_balance', 
            'currency', 
            'total_earnings', 
            'total_withdrawn'
        ]
        read_only_fields = fields


class WalletTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = WalletTransaction
        fields = [
            'id', 'transaction_type', 'source', 'amount', 'transaction_rate',
            'balance_before', 'balance_after', 'reference', 'description', 'created_at'
        ]
        read_only_fields = fields


class WithdrawalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Withdrawal
        fields = [
            'id', 'amount', 'status', 'payout_method', 'account_holder_name',
            'account_number', 'bank_name', 'bank_uuid', 'bank_branch',
            'requested_at', 'processed_at', 'rejection_reason'
        ]
        read_only_fields = ['id', 'status', 'requested_at', 'processed_at', 'rejection_reason']


class WithdrawalCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Withdrawal
        fields = [
            'amount', 'payout_method', 'account_holder_name',
            'account_number', 'bank_name', 'bank_uuid', 'bank_branch'
        ]

    def validate_account_number(self, value):
        cleaned = value.strip()
        # Allows digits and optional leading plus sign (8 to 20 chars)
        if not re.match(r'^\+?[0-9]{8,20}$', cleaned):
            raise serializers.ValidationError(
                "Invalid account or phone number format. Provide 8 to 20 digits."
            )
        return cleaned

    def validate_account_holder_name(self, value):
        cleaned = value.strip()
        if len(cleaned) < 3:
            raise serializers.ValidationError("Account holder name must be at least 3 characters.")
        # Restrict name to standard alphabetic characters and spaces
        if not re.match(r"^[a-zA-Z\s\.\'-]+$", cleaned):
            raise serializers.ValidationError("Account holder name contains invalid characters.")
        return cleaned

    def validate(self, data):
        user = self.context['request'].user
        wallet = Wallet.objects.get(user=user)

        if data['amount'] > wallet.balance:
            raise serializers.ValidationError({"amount": "Insufficient wallet balance."})

        payout_method = data.get('payout_method')
        account_number = data.get('account_number', '')

        # Mobile Money Validation (Malawi Airtel/TNM Mpamba format)
        if payout_method == 'mobile_money':
            if not re.match(r'^(265|0)?(88|99|98|89)[0-9]{7}$', account_number):
                raise serializers.ValidationError({
                    "account_number": "Invalid Mobile Money number. Expected a valid Airtel or TNM number."
                })

        # Bank Transfer Validation
        if payout_method == 'bank_transfer':
            if not data.get('bank_uuid'):
                raise serializers.ValidationError({
                    "bank_uuid": "Bank UUID is required for bank transfers."
                })

        return data