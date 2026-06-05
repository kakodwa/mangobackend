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


# serializers.py

class WithdrawalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Withdrawal
        fields = [
            'id', 
            'amount', 
            'status', 
            'payout_method',      
            'account_holder_name', 
            'account_number',       
            'bank_name', 
            'bank_uuid',       
            'bank_branch', 
            'requested_at', 
            'processed_at', 
            'rejection_reason'
        ]
        read_only_fields = ['id', 'status', 'requested_at', 'processed_at', 'rejection_reason']


class WithdrawalCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Withdrawal
        fields = ['amount', 'payout_method', 'account_holder_name', 'account_number', 'bank_name', 'bank_uuid', 'bank_branch']

    def validate(self, data):
        user = self.context['request'].user
        wallet = Wallet.objects.get(user=user)
        
        if data['amount'] > wallet.balance:
            raise serializers.ValidationError({"amount": "Insufficient balance"})
            
        if data['payout_method'] == 'bank_transfer' and not data.get('bank_uuid'):
            raise serializers.ValidationError({"bank_uuid": "Bank UUID is required for bank transfers."})
            
        return data
