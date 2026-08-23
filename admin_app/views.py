from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db.models import Q, Count
import json
from datetime import datetime, timedelta

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

from wallet.models import Wallet, WalletTransaction, Withdrawal,CompanyWallet
from payments.services.paychangu_service import PayChanguService 

from django.conf import settings

from analytics.views import get_dashboard_analytics

from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.views import View
from django.utils import timezone
from datetime import datetime, timedelta
from django.db.models.functions import TruncDay
from django.views.generic import TemplateView
from django.shortcuts import get_object_or_404, redirect
from django.db.models import Sum, Count
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin


from django.views.decorators.csrf import csrf_exempt
import json
from .models import SMSQueue

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
        
        # A. MAIN SYSTEM COUNTERS (OVERVIEW CARDS)
        # 1. Company Vault / Wallet metrics
        company_wallet = CompanyWallet.objects.first()
        context['company_wallet'] = company_wallet

        # 2. Total Order Count
        context['total_orders'] = Order.objects.count()

        # 3. Total Property Unlocks Count
        context['total_unlocks'] = PropertyUnlock.objects.count()

        # 4. Escrow Held Balance Calculation
        # Sums all active EscrowWallet entries where status is explicitly 'held'
        context['escrow_total'] = EscrowWallet.objects.filter(status='held').aggregate(total=Sum('amount'))['total'] or 0

        # B. TABULAR DATA REGISTRIES (TAB PANELS)
        # Orders Section Layout Data
        context['orders_list'] = Order.objects.select_related('customer').order_by('-created_at')[:10]

        # Shops & Marketplace Layout Data
        context['top_vendors'] = Shop.objects.select_related('owner').filter(status='approved')[:5]
        context['products_list'] = Product.objects.select_related('shop').order_by('-created_at')[:10]

        # Real Estate Listings Layout Data
        context['properties_list'] = Property.objects.select_related('owner').order_by('-created_at')[:10]

        # Financial Payouts Pipeline Data
        context['withdrawals_list'] = Withdrawal.objects.select_related('user').order_by('-requested_at')

        context['deliveries_list'] = Delivery.objects.select_related('order', 'seller', 'delivery_person').order_by('-created_at')[:10]
        context['delivery_people'] = DeliveryPerson.objects.all().order_by('-rating')[:5]

        chart_data = get_dashboard_analytics()
        context['chart_data_json'] =  json.dumps(chart_data)
        # --- Time-Series Configuration ---
        today = timezone.now().date()
        seven_days_ago = today - timedelta(days=6)
        days_range = [seven_days_ago + timedelta(days=i) for i in range(7)]
        
        context['chart_days'] = [day.strftime('%a') for day in days_range] 
        revenue_by_day = {day: 0 for day in days_range}
        escrow_by_day = {day: 0 for day in days_range}

        # Query 1: Order Revenue Grouped by Day (Order uses 'created_at')
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

        # FIXED Query 2: Escrow Wallet Grouped by Day (Traverses relationship to payment__created_at)
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

        # Map results to context keys expected by ApexCharts
        context['chart_revenue_volume'] = [revenue_by_day[day] for day in days_range]
        context['chart_escrow_data'] = [escrow_by_day[day] for day in days_range]

        return context

class ProcessWithdrawalActionView(AdminRequiredMixin, View):
    def post(self, request, pk, action_type):
        withdrawal = get_object_or_404(
            Withdrawal.objects.select_related('user'),
            pk=pk
        )

        # Prevent processing a withdrawal that has already been handled
        if withdrawal.status != 'pending':
            messages.error(
                request,
                "This withdrawal has already been processed."
            )
            return redirect('admin_app:admin_dashboard')

        # ==========================================================
        # APPROVE WITHDRAWAL
        # ==========================================================
        if action_type == 'approve':
            try:
                paychangu = PayChanguService()

                # Send payout according to the selected payout method
                if withdrawal.payout_method == 'mobile_money':
                    payout_response = paychangu.send_mobile_payout(withdrawal)
                else:
                    payout_response = paychangu.send_bank_payout(withdrawal)

                # Make sure we received a dictionary
                if not isinstance(payout_response, dict):
                    messages.error(
                        request,
                        "PayChangu returned an invalid response."
                    )
                    return redirect('admin_app:admin_dashboard')

                # Safely extract payout status
                payout_status = str(
                    payout_response.get('status', '')
                ).strip().lower()

                # Safely extract payout message
                payout_message = payout_response.get(
                    'message',
                    'API Error'
                )

                # A PayChangu message can sometimes be a dictionary
                if isinstance(payout_message, dict):
                    payout_message_display = json.dumps(
                        payout_message,
                        ensure_ascii=False
                    )
                else:
                    payout_message_display = str(payout_message)

                # --------------------------------------------------
                # Only approve when the gateway confirms success
                # --------------------------------------------------
                if payout_status in ['success', 'completed']:
                    withdrawal.status = 'approved'
                    withdrawal.processed_at = timezone.now()
                    withdrawal.save(
                        update_fields=[
                            'status',
                            'processed_at'
                        ]
                    )

                    messages.success(
                        request,
                        f"Payout of MWK {withdrawal.amount} "
                        f"approved and sent successfully."
                    )

                else:
                    # Gateway did not confirm successful payout
                    messages.error(
                        request,
                        f"PayChangu gateway failed: "
                        f"{payout_message_display}"
                    )

                    return redirect(
                        'admin_app:admin_dashboard'
                    )

            except Exception as e:
                # Prevent the admin page from crashing with a 500 error
                messages.error(
                    request,
                    f"Unable to process payout: {str(e)}"
                )

                return redirect(
                    'admin_app:admin_dashboard'
                )

        # ==========================================================
        # REJECT WITHDRAWAL
        # ==========================================================
        elif action_type == 'reject':
            try:
                with transaction.atomic():

                    # Lock the wallet while processing the refund
                    wallet = Wallet.objects.select_for_update().get(
                        user=withdrawal.user
                    )

                    # Store the balance before the refund
                    balance_before = wallet.balance

                    # Refund withdrawal amount
                    wallet.balance += withdrawal.amount

                    # Make sure total_withdrawn does not become negative
                    wallet.total_withdrawn = max(
                        wallet.total_withdrawn - withdrawal.amount,
                        0
                    )

                    wallet.save(
                        update_fields=[
                            'balance',
                            'total_withdrawn'
                        ]
                    )

                    # Mark withdrawal as rejected
                    withdrawal.status = 'rejected'
                    withdrawal.rejection_reason = (
                        "Rejected manually by administrator."
                    )
                    withdrawal.processed_at = timezone.now()

                    withdrawal.save(
                        update_fields=[
                            'status',
                            'rejection_reason',
                            'processed_at'
                        ]
                    )

                    # Record the refunded amount in wallet transactions
                    WalletTransaction.objects.create(
                        wallet=wallet,
                        transaction_type='credit',
                        source='withdrawal_refund',
                        amount=withdrawal.amount,
                        balance_before=balance_before,
                        balance_after=wallet.balance,
                        reference=f"WD-REF-{withdrawal.id}",
                        description=(
                            f"Refund for rejected withdrawal "
                            f"#{withdrawal.id}"
                        )
                    )

                messages.warning(
                    request,
                    f"Payout #{withdrawal.id} rejected. "
                    f"Funds returned to the user's wallet."
                )

            except Wallet.DoesNotExist:
                messages.error(
                    request,
                    "The user's wallet could not be found. "
                    "The withdrawal was not rejected."
                )

            except Exception as e:
                messages.error(
                    request,
                    f"Unable to reject withdrawal: {str(e)}"
                )

        # ==========================================================
        # INVALID ACTION
        # ==========================================================
        else:
            messages.error(
                request,
                "Invalid withdrawal action."
            )

        return redirect('admin_app:admin_dashboard')


#______________________________________________________________________

class AdminLoginView(View):
    template_name = 'admin_app/admin_login.html'

    def get(self, request):
        # If already authenticated as staff, skip login and go to dashboard
        if request.user.is_authenticated and request.user.is_staff:
            return redirect('admin_app:dashboard')
        return render(request, self.template_name)

    def post(self, request):
        # Extract credentials from your HTML form fields
        username_or_email = request.POST.get('username')
        password = request.POST.get('password')
        remember_me = request.POST.get('remember')

        # 1. Authenticate user credentials
        user = authenticate(request, username=username_or_email, password=password)

        if user is not None:
            # 2. Strict Guardrail: Verify administrative clearance
            if user.is_staff or user.is_superuser:
                login(request, user)
                
                # 3. Handle session expiry for 'Remember me' checkbox
                if not remember_me:
                    request.session.set_expiry(0) # Session expires when browser closes
                else:
                    request.session.set_expiry(1209600) # Session persists for 2 weeks
                
                messages.success(request, f"Welcome back, {user.username}!")
                return redirect('admin_app:admin_dashboard') # Name of your dashboard URL route
            else:
                # Regular user trying to breach the admin panel portal
                messages.error(request, "Access Denied: Insufficient security clearance privileges.")
        else:
            # Invalid credentials
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
    
    # Lock fetched messages
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