from rest_framework import serializers
from .models import Wallet, WalletTransaction, Withdrawal


class WalletSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wallet
        fields = ['id', 'balance', 'currency', 'total_earnings', 'total_withdrawn']
        read_only_fields = fields


class WalletTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = WalletTransaction
        fields = ['id', 'transaction_type', 'source', 'amount','transaction_rate','balance_before', 
                  'balance_after', 'reference', 'description', 'created_at']
        read_only_fields = fields


class WithdrawalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Withdrawal
        fields = ['id', 'amount', 'status', 'account_holder_name', 'bank_account_number',
                  'bank_name', 'bank_branch', 'requested_at', 'processed_at', 'rejection_reason']
        read_only_fields = ['id', 'status', 'requested_at', 'processed_at', 'rejection_reason']


class WithdrawalCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Withdrawal
        fields = ['amount', 'account_holder_name', 'bank_account_number', 'bank_name', 'bank_branch']

    def validate_amount(self, value):
        user = self.context['request'].user
        wallet = Wallet.objects.get(user=user)
        if value > wallet.balance:
            raise serializers.ValidationError("Insufficient balance")
        return value

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)
