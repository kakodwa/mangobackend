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
from wallet.models import Withdrawal,CompanyWallet
from payments.models import EscrowWallet

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
from django.contrib.auth.mixins import UserPassesTestMixin



class AdminRequiredMixin(UserPassesTestMixin):
    """Restricts access only to Authorized Staff/Global Admins."""
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_staff


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
    """
    Action engine to process or drop pending withdrawal claims from the platform UI.
    """
    def post(self, request, pk, action_type):
        withdrawal = get_object_or_404(Withdrawal, pk=pk)
        
        if withdrawal.status != 'pending':
            messages.error(request, "This claim context has already been settled and closed.")
            return redirect('admin_app:admin_dashboard')

        if action_type == 'approve':
            withdrawal.status = 'approved'
            # Hook your system-wide PayChangu transfer routines right here if necessary
            messages.success(request, f"Payout request for {withdrawal.account_holder_name} was approved.")
        elif action_type == 'reject':
            withdrawal.status = 'rejected'
            messages.warning(request, "Payout request has been successfully rejected.")
            
        withdrawal.save()
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