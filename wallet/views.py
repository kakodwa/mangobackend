# views.py

from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.db import transaction

from .models import Wallet, WalletTransaction, Withdrawal
from payments.services.paychangu_service import PayChanguService 
from .serializers import (
    WalletSerializer, 
    WalletTransactionSerializer, 
    WithdrawalSerializer, 
    WithdrawalCreateSerializer
)


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
                
                # 2. Save the local withdrawal entry status as 'pending'
                withdrawal = serializer.save(user=request.user)
                
                # 3. Handle local bookkeeping records
                balance_before = wallet.balance
                balance_after = wallet.balance - amount
                
                wallet.balance = balance_after
                wallet.total_withdrawn += amount
                wallet.save()
                
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
            # 🚀 PAYCHANGU DISBURSEMENT INITIALIZATION
            # ========================================================
            paychangu = PayChanguService()
            
            if payout_method == 'mobile_money':
                payout_response = paychangu.send_mobile_payout(withdrawal)
            else:
                payout_response = paychangu.send_bank_payout(withdrawal)

            # Extract and normalize PayChangu's status response string
            payout_status = str(payout_response.get('status', '')).lower()
            payout_message = payout_response.get('message', '')

            # Check if PayChangu successfully accepted and queued payout request
            if payout_status in ['success', 'completed'] or 'successfully' in payout_message.lower():
                withdrawal.status = 'approved' 
                withdrawal.save()
                return Response(WithdrawalSerializer(withdrawal).data, status=status.HTTP_201_CREATED)
            else:
                # Local recovery refund if initial gateway handoff fails
                self._refund_wallet(wallet.id, amount, withdrawal)
                return Response({
                    "error": "PayChangu payout initialization failed", 
                    "details": payout_response.get('message', 'Unknown API Error')
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response({"error": f"An internal error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _refund_wallet(self, wallet_id, amount, withdrawal):
        """Helper logic to revert funds if the payout gateway drops out"""
        with transaction.atomic():
            w = Wallet.objects.select_for_update().get(id=wallet_id)
            w.balance += amount
            w.total_withdrawn -= amount
            w.save()
            
            withdrawal.status = 'rejected'
            withdrawal.rejection_reason = "PayChangu gateway rejection."
            withdrawal.save()