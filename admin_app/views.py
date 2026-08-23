import os
import sys
import json
import logging
from decimal import Decimal
from datetime import datetime, timedelta

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db.models import Q, Count, Sum
from django.db.models.functions import TruncDay
from django.views.generic import TemplateView
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.views import View
from django.utils import timezone
from django.db import transaction
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

# Models Import
from users.models import User, Address
from shops.models import Shop, ShopReview
from products.models import Product, ProductReview
from realestate.models import Property, PropertyUnlock
from delivery.models import Delivery, DeliveryPerson, DeliveryRating
from hospitality.models import Lodge, Room, Booking, Review as LodgeReview, Amenity
from events.models import Event, EventTicketType, Ticket, TicketCheckIn
from orders.models import Order
from payments.models import EscrowWallet

from wallet.models import Wallet, WalletTransaction, Withdrawal, CompanyWallet
from payments.services.paychangu_service import PayChanguService 
from analytics.views import get_dashboard_analytics
from .models import SMSQueue

logger = logging.getLogger(__name__)


def log_debug(message):
    """
    Standardized logger that routes messages to standard error (Phusion Passenger)
    and Django's configured logging module.
    """
    formatted_msg = f"[ADMIN_PAYOUT] {message}"
    logger.info(formatted_msg)
    sys.stderr.write(f"[{timezone.now().strftime('%Y-%m-%d %H:%M:%S')}] {formatted_msg}\n")
    sys.stderr.flush()


def calculate_paychangu_fee(amount, payout_method):
    """Calculates actual PayChangu processing fee charged to your merchant vault."""
    amt = Decimal(str(amount))
    if payout_method == 'mobile_money':
        return amt * Decimal('0.018')
    else:
        return (amt * Decimal('0.015')) + Decimal('700.00')


class AdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    login_url = 'admin_app:admin_login'
    redirect_field_name = 'next'

    def test_func(self):
        return self.request.user.is_staff

    def handle_no_permission(self):
        messages.error(
            self.request,
            "You must be logged in as an administrator."
        )
        return redirect(self.login_url)


class AdminDashboardView(AdminRequiredMixin, TemplateView):
    template_name = 'console/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # --- System Counters & Lists ---
        company_wallet = CompanyWallet.objects.first()
        context['company_wallet'] = company_wallet

        context['total_orders'] = Order.objects.count()
        context['total_unlocks'] = PropertyUnlock.objects.count()
        context['escrow_total'] = EscrowWallet.objects.filter(status='held').aggregate(total=Sum('amount'))['total'] or 0

        # B. TABULAR DATA REGISTRIES (TAB PANELS)
        context['orders_list'] = Order.objects.select_related('customer').order_by('-created_at')[:10]
        context['top_vendors'] = Shop.objects.select_related('owner').filter(status='approved')[:5]
        context['products_list'] = Product.objects.select_related('shop').order_by('-created_at')[:10]
        context['properties_list'] = Property.objects.select_related('owner').order_by('-created_at')[:10]
        context['withdrawals_list'] = Withdrawal.objects.select_related('user').order_by('-requested_at')
        context['deliveries_list'] = Delivery.objects.select_related('order', 'seller', 'delivery_person').order_by('-created_at')[:10]
        context['delivery_people'] = DeliveryPerson.objects.all().order_by('-rating')[:5]

        chart_data = get_dashboard_analytics()
        context['chart_data_json'] = json.dumps(chart_data)

        # --- Time-Series Configuration ---
        today = timezone.now().date()
        seven_days_ago = today - timedelta(days=6)
        days_range = [seven_days_ago + timedelta(days=i) for i in range(7)]
        
        context['chart_days'] = [day.strftime('%a') for day in days_range] 
        revenue_by_day = {day: 0 for day in days_range}
        escrow_by_day = {day: 0 for day in days_range}

        # Query 1: Order Revenue Grouped by Day
        order_totals = (
            Order.objects.filter(created_at__date__gte=seven_days_ago)
            .annotate(day=TruncDay('created_at'))
            .values('day')
            .annotate(daily_revenue=Sum('total_amount'))
            .order_by('day')
        )
        for entry in order_totals:
            entry_date = entry['day'].date()
            if entry_date in revenue_by_day:
                revenue_by_day[entry_date] = float(entry['daily_revenue'] or 0)

        # Query 2: Escrow Wallet Grouped by Day
        escrow_totals = (
            EscrowWallet.objects.filter(payment__created_at__date__gte=seven_days_ago, status='held')
            .annotate(day=TruncDay('payment__created_at'))
            .values('day')
            .annotate(daily_escrow=Sum('amount'))
            .order_by('day')
        )
        for entry in escrow_totals:
            entry_date = entry['day'].date()
            if entry_date in escrow_by_day:
                escrow_by_day[entry_date] = float(entry['daily_escrow'] or 0)

        context['chart_revenue_volume'] = [revenue_by_day[day] for day in days_range]
        context['chart_escrow_data'] = [escrow_by_day[day] for day in days_range]

        return context


class ProcessWithdrawalActionView(AdminRequiredMixin, View):
    def post(self, request, pk, action_type):
        log_debug(f"POST request received for PK: {pk}, Action: {action_type}")

        withdrawal = get_object_or_404(
            Withdrawal.objects.select_related('user'),
            pk=pk
        )

        if withdrawal.status != 'pending':
            log_debug(f"FAILED: Status is '{withdrawal.status}', not 'pending'.")
            messages.error(request, f"This withdrawal has already been processed (Status: {withdrawal.status}).")
            return redirect('admin_app:admin_dashboard')

        # APPROVE WITHDRAWAL (REQUIRES ADMIN PASSWORD RE-VERIFICATION)
        if action_type == 'approve':
            admin_password = request.POST.get('admin_password')

            if not admin_password:
                messages.error(request, "Security Clearance Required: Admin password must be provided.")
                return redirect('admin_app:admin_dashboard')

            # Re-verify admin credentials before releasing funds
            if not request.user.check_password(admin_password):
                log_debug(f"SECURITY ALERT: Failed password verification by admin '{request.user.username}' for withdrawal #{withdrawal.id}")
                messages.error(request, "Access Denied: Invalid security password.")
                return redirect('admin_app:admin_dashboard')

            try:
                paychangu = PayChanguService()

                if withdrawal.payout_method == 'mobile_money':
                    payout_response = paychangu.send_mobile_payout(withdrawal)
                else:
                    payout_response = paychangu.send_bank_payout(withdrawal)

                log_debug(f"Raw PayChangu Response: {payout_response}")

                if not isinstance(payout_response, dict):
                    messages.error(request, "PayChangu returned an invalid response.")
                    return redirect('admin_app:admin_dashboard')

                payout_status = str(payout_response.get('status', '')).strip().lower()
                payout_message = payout_response.get('message', 'API Error')
                payout_message_display = json.dumps(payout_message) if isinstance(payout_message, dict) else str(payout_message)

                if payout_status in ['success', 'completed', 'pending'] or 'successfully' in payout_message_display.lower():
                    withdrawal.status = 'approved'
                    withdrawal.processed_at = timezone.now()
                    withdrawal.save(update_fields=['status', 'processed_at'])

                    # Deduct actual PayChangu fee from the Company Wallet reserve buffer
                    company_wallet = CompanyWallet.objects.first()
                    if company_wallet:
                        actual_fee = calculate_paychangu_fee(withdrawal.amount, withdrawal.payout_method)
                        company_wallet.record_payout_gateway_fee(actual_fee)

                    log_debug(f"SUCCESS: Payout queued/approved for Withdrawal #{withdrawal.id}")
                    messages.success(request, f"Payout of MWK {withdrawal.amount} sent to PayChangu processing queue.")
                else:
                    log_debug(f"GATEWAY REJECTION: Status={payout_status}, Message={payout_message_display}")
                    messages.error(request, f"PayChangu gateway failed: {payout_message_display}")

            except Exception as e:
                import traceback
                log_debug(f"EXCEPTION IN APPROVAL: {str(e)}")
                logger.error(traceback.format_exc())
                messages.error(request, f"Unable to process payout: {str(e)}")

        # REJECT WITHDRAWAL
        elif action_type == 'reject':
            try:
                with transaction.atomic():
                    wallet = Wallet.objects.select_for_update().get(user=withdrawal.user)
                    balance_before = wallet.balance
                    wallet.balance += withdrawal.amount
                    wallet.total_withdrawn = max(wallet.total_withdrawn - withdrawal.amount, Decimal('0.00'))
                    wallet.save(update_fields=['balance', 'total_withdrawn'])

                    withdrawal.status = 'rejected'
                    withdrawal.rejection_reason = "Rejected manually by administrator."
                    withdrawal.processed_at = timezone.now()
                    withdrawal.save(update_fields=['status', 'rejection_reason', 'processed_at'])

                    WalletTransaction.objects.create(
                        wallet=wallet,
                        transaction_type='credit',
                        source='withdrawal_refund',
                        amount=withdrawal.amount,
                        balance_before=balance_before,
                        balance_after=wallet.balance,
                        reference=f"WD-REF-{withdrawal.id}",
                        description=f"Refund for rejected withdrawal #{withdrawal.id}"
                    )

                log_debug(f"REJECTED: Withdrawal #{withdrawal.id} refunded.")
                messages.warning(request, f"Payout #{withdrawal.id} rejected. Funds returned to user wallet.")

            except Exception as e:
                import traceback
                log_debug(f"EXCEPTION IN REJECTION: {str(e)}")
                logger.error(traceback.format_exc())
                messages.error(request, f"Unable to reject withdrawal: {str(e)}")

        return redirect('admin_app:admin_dashboard')


class AdminLoginView(View):
    template_name = 'admin_app/admin_login.html'

    def get(self, request):
        if request.user.is_authenticated and request.user.is_staff:
            return redirect('admin_app:admin_dashboard')
        return render(request, self.template_name)

    def post(self, request):
        username_or_email = request.POST.get('username')
        password = request.POST.get('password')
        remember_me = request.POST.get('remember')

        user = authenticate(request, username=username_or_email, password=password)

        if user is not None:
            if user.is_staff or user.is_superuser:
                login(request, user)
                
                if not remember_me:
                    request.session.set_expiry(0)
                else:
                    request.session.set_expiry(1209600)
                
                messages.success(request, f"Welcome back, {user.username}!")
                return redirect('admin_app:admin_dashboard')
            else:
                messages.error(request, "Access Denied: Insufficient security clearance privileges.")
        else:
            messages.error(request, "Invalid identification identifier or security passphrase.")

        return render(request, self.template_name)


def admin_logout(request):
    logout(request)
    messages.info(request, "Logged out securely.")
    return redirect('admin_app:admin_login')


def get_pending_sms(request):
    if request.headers.get('X-Api-Key') != settings.SMS_API_KEY:
        return JsonResponse({'error': 'Unauthorized'}, status=401)
        
    pending = SMSQueue.objects.filter(status='QUEUED')[:10]
    data = [{'id': m.id, 'phone_number': m.phone_number, 'message': m.message} for m in pending]
    
    SMSQueue.objects.filter(id__in=[m.id for m in pending]).update(status='PROCESSING')
    return JsonResponse(data, safe=False)


@csrf_exempt
def mark_sms_sent(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        if request.headers.get('X-Api-Key') != settings.SMS_API_KEY:
            return JsonResponse({'error': 'Unauthorized'}, status=401)
            
        SMSQueue.objects.filter(id=data.get('sms_id')).update(status=data.get('status', 'SENT'))
        return JsonResponse({'status': 'updated'})
    return JsonResponse({'error': 'Method not allowed'}, status=405)