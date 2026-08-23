# views.py

from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.db import transaction
from django.utils import timezone

from .models import Wallet, WalletTransaction, Withdrawal
from payments.services.paychangu_service import PayChanguService 
from .serializers import (
    WalletSerializer, 
    WalletTransactionSerializer, 
    WithdrawalSerializer, 
    WithdrawalCreateSerializer
)

# Threshold limit for automated disbursements
AUTO_PAYOUT_LIMIT = 50000.00


class StandardResultsSetPagination(PageNumberPagination):
    """Custom pagination configuration for wallet records."""
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class WalletViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=['get'])
    def balance(self, request):
        """Get user wallet balance"""
        wallet, created = Wallet.objects.get_or_create(user=request.user)
        serializer = WalletSerializer(wallet)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def transactions(self, request):
        """Get paginated wallet transactions"""
        wallet, created = Wallet.objects.get_or_create(user=request.user)
        transactions = wallet.transactions.all()
        
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(transactions, request)
        
        if page is not None:
            serializer = WalletTransactionSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        serializer = WalletTransactionSerializer(transactions, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def withdrawals(self, request):
        """Get user withdrawals"""
        withdrawals = Withdrawal.objects.filter(user=request.user)
        
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(withdrawals, request)
        
        if page is not None:
            serializer = WithdrawalSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        serializer = WithdrawalSerializer(withdrawals, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def request_withdrawal(self, request):
        serializer = WithdrawalCreateSerializer(data=request.data, context={'request': request})
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        amount = serializer.validated_data['amount']
        payout_method = serializer.validated_data['payout_method']
        
        try:
            with transaction.atomic():
                # 1. Lock wallet row in database to prevent concurrent requests
                wallet = Wallet.objects.select_for_update().get(user=request.user)
                
                if wallet.balance < amount:
                    return Response({"error": "Insufficient balance"}, status=status.HTTP_400_BAD_REQUEST)
                
                # 2. Hold funds and create local record with 'pending' status
                balance_before = wallet.balance
                balance_after = wallet.balance - amount
                
                wallet.balance = balance_after
                wallet.total_withdrawn += amount
                wallet.save()
                
                withdrawal = serializer.save(user=request.user, status='pending')
                
                # 3. Create debit ledger transaction entry
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

            # ========================================================
            # 🛡️ ROUTING RULE 1: HIGH-VALUE TRANSACTION ROUTE (>= MWK 50,000)
            # ========================================================
            if amount >= AUTO_PAYOUT_LIMIT:
                return Response({
                    "message": f"Withdrawal request of MWK {amount:.2f} logged. Requires administrative approval for amounts over MWK {AUTO_PAYOUT_LIMIT:,.2f}.",
                    "data": WithdrawalSerializer(withdrawal).data
                }, status=status.HTTP_201_CREATED)

            # ========================================================
            # 🚀 ROUTING RULE 2: AUTOMATED LOW-VALUE DISBURSEMENT (< MWK 50,000)
            # ========================================================
            paychangu = PayChanguService()
            
            if payout_method == 'mobile_money':
                payout_response = paychangu.send_mobile_payout(withdrawal)
            else:
                payout_response = paychangu.send_bank_payout(withdrawal)

            payout_status = str(payout_response.get('status', '')).lower()
            payout_message = payout_response.get('message', '')

            # Check if PayChangu accepted the transfer
            if payout_status in ['success', 'completed'] or 'successfully' in payout_message.lower():
                withdrawal.status = 'approved' 
                withdrawal.processed_at = timezone.now()
                withdrawal.save()
                return Response(WithdrawalSerializer(withdrawal).data, status=status.HTTP_201_CREATED)
            else:
                # ROUTING RULE 3: GATEWAY FAIL FALLBACK
                # Flag for admin panel review rather than rejecting/refunding immediately
                withdrawal.rejection_reason = f"Automated gateway dispatch failed: {payout_response.get('message', 'Gateway Error')}"
                withdrawal.save()
                
                return Response({
                    "message": "Automated payout dispatch failed. Request queued for administrative review.",
                    "data": WithdrawalSerializer(withdrawal).data
                }, status=status.HTTP_202_ACCEPTED)
                
        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response({"error": f"An internal error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _refund_wallet(self, wallet_id, amount, withdrawal, reason="PayChangu gateway rejection."):
        """Helper logic to revert funds if a withdrawal is dropped or rejected"""
        with transaction.atomic():
            w = Wallet.objects.select_for_update().get(id=wallet_id)
            w.balance += amount
            w.total_withdrawn -= amount
            w.save()
            
            withdrawal.status = 'rejected'
            withdrawal.rejection_reason = reason
            withdrawal.processed_at = timezone.now()
            withdrawal.save()

            WalletTransaction.objects.create(
                wallet=w,
                transaction_type='credit',
                source='withdrawal_refund',
                amount=amount,
                balance_before=w.balance - amount,
                balance_after=w.balance,
                reference=f"WD-REF-{withdrawal.id}",
                description=f"Refund for rejected withdrawal #{withdrawal.id}"
            )