import os
import sys
import json
from decimal import Decimal
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action, throttle_classes
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework.throttling import ScopedRateThrottle
from django.db import transaction
from django.utils import timezone

from .models import Wallet, WalletTransaction, Withdrawal, CompanyWallet
from payments.services.paychangu_service import PayChanguService 
from .serializers import (
    WalletSerializer, 
    WalletTransactionSerializer, 
    WithdrawalSerializer, 
    WithdrawalCreateSerializer
)

AUTO_PAYOUT_LIMIT = 500000.00


def calculate_paychangu_fee(amount, payout_method):
    amt = Decimal(str(amount))
    if payout_method == 'mobile_money':
        return amt * Decimal('0.018')
    else:
        return (amt * Decimal('0.015')) + Decimal('700.00')


class WithdrawalThrottle(ScopedRateThrottle):
    throttle_scope = 'withdrawals'


class WalletViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=['get'])
    def balance(self, request):
        wallet, created = Wallet.objects.get_or_create(user=request.user)
        serializer = WalletSerializer(wallet)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def transactions(self, request):
        wallet, created = Wallet.objects.get_or_create(user=request.user)
        transactions = wallet.transactions.all()
        paginator = PageNumberPagination()
        page = paginator.paginate_queryset(transactions, request)
        if page is not None:
            serializer = WalletTransactionSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)
        serializer = WalletTransactionSerializer(transactions, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def withdrawals(self, request):
        withdrawals = Withdrawal.objects.filter(user=request.user)
        paginator = PageNumberPagination()
        page = paginator.paginate_queryset(withdrawals, request)
        if page is not None:
            serializer = WithdrawalSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)
        serializer = WalletTransactionSerializer(withdrawals, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'], throttle_classes=[WithdrawalThrottle])
    def request_withdrawal(self, request):
        serializer = WithdrawalCreateSerializer(data=request.data, context={'request': request})
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        amount = serializer.validated_data['amount']
        payout_method = serializer.validated_data['payout_method']
        
        try:
            with transaction.atomic():
                wallet = Wallet.objects.select_for_update().get(user=request.user)
                
                if wallet.balance < amount:
                    return Response({"error": "Insufficient balance"}, status=status.HTTP_400_BAD_REQUEST)
                
                balance_before = wallet.balance
                balance_after = wallet.balance - amount
                
                wallet.balance = balance_after
                wallet.total_withdrawn += amount
                wallet.save()
                
                withdrawal = serializer.save(user=request.user, status='pending')
                
                WalletTransaction.objects.create(
                    wallet=wallet,
                    transaction_type='debit',
                    source='withdrawal',
                    amount=amount,
                    balance_before=balance_before,
                    balance_after=balance_after,
                    reference=f"WD-REQ-{withdrawal.id}",
                    description=f"Withdrawal via {payout_method} initiated"
                )

            if amount >= AUTO_PAYOUT_LIMIT:
                return Response({
                    "message": f"Withdrawal request of MWK {amount:.2f} logged. Requires administrative approval.",
                    "data": WithdrawalSerializer(withdrawal).data
                }, status=status.HTTP_201_CREATED)

            paychangu = PayChanguService()
            
            if payout_method == 'mobile_money':
                payout_response = paychangu.send_mobile_payout(withdrawal)
            else:
                payout_response = paychangu.send_bank_payout(withdrawal)

            if not isinstance(payout_response, dict):
                withdrawal.rejection_reason = "Automated gateway error: Invalid response format."
                withdrawal.save()
                return Response({
                    "message": "Automated payout dispatch failed. Queued for admin review.",
                    "data": WithdrawalSerializer(withdrawal).data
                }, status=status.HTTP_202_ACCEPTED)

            payout_status = str(payout_response.get('status', '')).strip().lower()
            payout_message = str(payout_response.get('message', ''))

            if payout_status in ['success', 'completed', 'pending'] or 'successfully' in payout_message.lower():
                withdrawal.status = 'approved' 
                withdrawal.processed_at = timezone.now()
                withdrawal.save(update_fields=['status', 'processed_at'])

                company_wallet = CompanyWallet.objects.first()
                if company_wallet:
                    actual_fee = calculate_paychangu_fee(amount, payout_method)
                    company_wallet.record_payout_gateway_fee(actual_fee)

                return Response(WithdrawalSerializer(withdrawal).data, status=status.HTTP_201_CREATED)
            else:
                withdrawal.rejection_reason = f"Gateway dispatch failed: {payout_message}"
                withdrawal.save(update_fields=['rejection_reason'])
                return Response({
                    "message": "Automated payout dispatch failed. Queued for admin review.",
                    "data": WithdrawalSerializer(withdrawal).data
                }, status=status.HTTP_202_ACCEPTED)
                
        except Exception as e:
            return Response({"error": f"Internal server error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)