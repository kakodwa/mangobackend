from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Wallet, WalletTransaction, Withdrawal
from payments.services.paychangu_service import PayChanguService 
from django.db import transaction 
from .serializers import WalletSerializer, WalletTransactionSerializer, WithdrawalSerializer, WithdrawalCreateSerializer


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
        """Get wallet transactions"""
        wallet, created = Wallet.objects.get_or_create(user=request.user)
        print("Wallet Balance:", wallet.balance)
        print("Wallet ID:", wallet.id)
        print("User:", request.user.username)
        transactions = wallet.transactions.all()
        serializer = WalletTransactionSerializer(transactions, many=True)
        return Response(serializer.data)


    @action(detail=False, methods=['get'])
    def withdrawals(self, request):
        """Get user withdrawals"""
        withdrawals = Withdrawal.objects.filter(user=request.user)
        serializer = WithdrawalSerializer(withdrawals, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def request_withdrawal(self, request):
        print("RAW DATA FROM FLUTTER:", request.data)
        serializer = WithdrawalCreateSerializer(data=request.data, context={'request': request})
        
        if not serializer.is_valid():
            print("SERIALIZER ERRORS:", serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        amount = serializer.validated_data['amount']
        payout_method = serializer.validated_data['payout_method']
        
        try:
            with transaction.atomic():
                # 1. Lock wallet row in the database so no concurrent requests can mess with it
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

            # Check if PayChangu successfully accepted and queued the payout request
            if payout_status in ['success', 'completed'] or 'successfully' in payout_message.lower():
                # ✅ Keep it as 'approved' (meaning handoff succeeded). 
                # The Master Webhook will switch this to 'processed' once the money hits their phone!
                withdrawal.status = 'approved' 
                withdrawal.save()
                return Response(WithdrawalSerializer(withdrawal).data, status=status.HTTP_201_CREATED)
            else:
                # If PayChangu rejected the raw data setup layout right away, execute local recovery refund
                self._refund_wallet(wallet.id, amount, withdrawal)
                return Response({
                    "error": "PayChangu payout initialization failed", 
                    "details": payout_response.get('message', 'Unknown API Error')
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            import traceback
            print("❌ WITHDRAWAL CRASHED WITH ERROR:", str(e))
            traceback.print_exc()
            return Response({"error": f"An internal error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


    def _refund_wallet(self, wallet_id, amount, withdrawal):
        """Helper logic to revert funds if the payout gateway immediately drops out"""
        with transaction.atomic():
            w = Wallet.objects.select_for_update().get(id=wallet_id)
            w.balance += amount
            w.total_withdrawn -= amount
            w.save()
            
            withdrawal.status = 'rejected'
            withdrawal.rejection_reason = "PayChangu gateway rejection."
            withdrawal.save()



