# views.py

import os
import sys
import json
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.db import transaction
from django.utils import timezone
from django.conf import settings

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


def log_debug(message):
    """
    Dual-logger: Writes directly to 'payout_debug.log' inside BASE_DIR
    and flushes to sys.stderr for Phusion Passenger.
    """
    formatted_msg = f"[{timezone.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}"
    
    sys.stderr.write(f"{formatted_msg}\n")
    sys.stderr.flush()

    try:
        log_path = os.path.join(settings.BASE_DIR, 'payout_debug.log')
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(f"{formatted_msg}\n")
    except Exception as e:
        sys.stderr.write(f"Failed to write to file log: {str(e)}\n")


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

        serializer = WalletTransactionSerializer(withdrawals, many=True)
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

            log_debug(f"[AUTO PAYOUT] User {request.user} requested withdrawal #{withdrawal.id} for MWK {amount}")

            # ========================================================
            # 🛡️ ROUTING RULE 1: HIGH-VALUE TRANSACTION ROUTE (>= MWK 50,000)
            # ========================================================
            if amount >= AUTO_PAYOUT_LIMIT:
                log_debug(f"[AUTO PAYOUT] Withdrawal #{withdrawal.id} exceeds threshold. Held for admin review.")
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

            log_debug(f"[AUTO PAYOUT] Raw PayChangu Response for #{withdrawal.id}: {payout_response}")

            if not isinstance(payout_response, dict):
                log_debug(f"[AUTO PAYOUT] ERROR: Response for #{withdrawal.id} is not a dict.")
                withdrawal.rejection_reason = "Automated gateway error: Invalid API response format."
                withdrawal.save()
                return Response({
                    "message": "Automated payout dispatch failed. Request queued for administrative review.",
                    "data": WithdrawalSerializer(withdrawal).data
                }, status=status.HTTP_202_ACCEPTED)

            payout_status = str(payout_response.get('status', '')).strip().lower()
            payout_message = payout_response.get('message', 'API Error')

            if isinstance(payout_message, dict):
                payout_message_display = json.dumps(payout_message, ensure_ascii=False)
            else:
                payout_message_display = str(payout_message)

            # ========================================================
            # ⚡ ROUTING RULE 3: CHECK PAYCHANGU ACCEPTANCE STATUS
            # ('pending', 'success', or 'completed' are valid gateway confirmations)
            # ========================================================
            if payout_status in ['success', 'completed', 'pending'] or 'successfully' in payout_message_display.lower():
                withdrawal.status = 'approved' 
                withdrawal.processed_at = timezone.now()
                withdrawal.save(update_fields=['status', 'processed_at'])
                log_debug(f"[AUTO PAYOUT] SUCCESS: Withdrawal #{withdrawal.id} approved and sent to PayChangu.")
                return Response(WithdrawalSerializer(withdrawal).data, status=status.HTTP_201_CREATED)
            else:
                # Flag for admin panel review rather than rejecting/refunding immediately
                log_debug(f"[AUTO PAYOUT] REJECTED BY GATEWAY: #{withdrawal.id} - Status={payout_status}, Message={payout_message_display}")
                withdrawal.rejection_reason = f"Automated gateway dispatch failed: {payout_message_display}"
                withdrawal.save(update_fields=['rejection_reason'])
                
                return Response({
                    "message": "Automated payout dispatch failed. Request queued for administrative review.",
                    "data": WithdrawalSerializer(withdrawal).data
                }, status=status.HTTP_202_ACCEPTED)
                
        except Exception as e:
            import traceback
            log_debug(f"[AUTO PAYOUT] EXCEPTION IN REQUEST_WITHDRAWAL: {str(e)}")
            log_debug(traceback.format_exc())
            return Response({"error": f"An internal error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _refund_wallet(self, wallet_id, amount, withdrawal, reason="PayChangu gateway rejection."):
        """Helper logic to revert funds if a withdrawal is dropped or rejected"""
        with transaction.atomic():
            w = Wallet.objects.select_for_update().get(id=wallet_id)
            w.balance += amount
            w.total_withdrawn = max(w.total_withdrawn - amount, 0)
            w.save(update_fields=['balance', 'total_withdrawn'])
            
            withdrawal.status = 'rejected'
            withdrawal.rejection_reason = reason
            withdrawal.processed_at = timezone.now()
            withdrawal.save(update_fields=['status', 'rejection_reason', 'processed_at'])

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