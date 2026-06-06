"""
Admin Dashboard Utility Functions
Helper functions for common admin operations
"""

from django.db.models import Count, Q, Avg, Sum
from datetime import datetime, timedelta
from django.utils import timezone

# Models Import
from users.models import User
from shops.models import Shop
from products.models import Product
from realestate.models import Property
from deliveries.models import Delivery
from lodges.models import Lodge, Booking, Room
from events.models import Event, Ticket

# ============================================
# STATISTICS HELPERS
# ============================================

class DashboardStatistics:
    """Generate comprehensive dashboard statistics"""
    
    @staticmethod
    def get_user_statistics():
        """Get user-related statistics"""
        return {
            'total': User.objects.count(),
            'verified': User.objects.filter(is_verified=True).count(),
            'active': User.objects.filter(is_active=True).count(),
            'by_type': User.objects.values('user_type').annotate(count=Count('id')),
        }
    
    @staticmethod
    def get_shop_statistics():
        """Get shop-related statistics"""
        return {
            'total': Shop.objects.count(),
            'pending': Shop.objects.filter(status='pending').count(),
            'approved': Shop.objects.filter(status='approved').count(),
            'rejected': Shop.objects.filter(status='rejected').count(),
            'suspended': Shop.objects.filter(status='suspended').count(),
            'avg_rating': Shop.objects.aggregate(Avg('rating'))['rating__avg'] or 0,
        }
    
    @staticmethod
    def get_product_statistics():
        """Get product-related statistics"""
        return {
            'total': Product.objects.count(),
            'active': Product.objects.filter(is_active=True).count(),
            'inactive': Product.objects.filter(is_active=False).count(),
            'low_stock': Product.objects.filter(stock__lt=10, stock__gt=0).count(),
            'out_of_stock': Product.objects.filter(stock=0).count(),
            'total_revenue': Product.objects.aggregate(
                Sum('price'))['price__sum'] or 0,
        }
    
    @staticmethod
    def get_delivery_statistics():
        """Get delivery-related statistics"""
        return {
            'total': Delivery.objects.count(),
            'pending': Delivery.objects.filter(status='pending').count(),
            'assigned': Delivery.objects.filter(status='assigned').count(),
            'in_transit': Delivery.objects.filter(status='in_transit').count(),
            'delivered': Delivery.objects.filter(status='delivered').count(),
            'failed': Delivery.objects.filter(status='failed').count(),
        }
    
    @staticmethod
    def get_booking_statistics():
        """Get booking-related statistics"""
        return {
            'total': Booking.objects.count(),
            'pending': Booking.objects.filter(booking_status='pending').count(),
            'confirmed': Booking.objects.filter(booking_status='confirmed').count(),
            'checked_in': Booking.objects.filter(booking_status='checked_in').count(),
            'completed': Booking.objects.filter(booking_status='checked_out').count(),
            'cancelled': Booking.objects.filter(booking_status='cancelled').count(),
            'total_revenue': Booking.objects.aggregate(
                Sum('total_amount'))['total_amount__sum'] or 0,
        }
    
    @staticmethod
    def get_event_statistics():
        """Get event-related statistics"""
        return {
            'total': Event.objects.count(),
            'draft': Event.objects.filter(status='draft').count(),
            'published': Event.objects.filter(status='published').count(),
            'cancelled': Event.objects.filter(status='cancelled').count(),
            'completed': Event.objects.filter(status='completed').count(),
            'featured': Event.objects.filter(is_featured=True).count(),
        }
    
    @staticmethod
    def get_ticket_statistics():
        """Get ticket-related statistics"""
        return {
            'total': Ticket.objects.count(),
            'pending': Ticket.objects.filter(payment_status='pending').count(),
            'paid': Ticket.objects.filter(payment_status='paid').count(),
            'failed': Ticket.objects.filter(payment_status='failed').count(),
            'cancelled': Ticket.objects.filter(payment_status='cancelled').count(),
            'total_revenue': Ticket.objects.filter(
                payment_status='paid').aggregate(
                Sum('total_amount'))['total_amount__sum'] or 0,
        }
    
    @staticmethod
    def get_all_statistics():
        """Get all dashboard statistics"""
        return {
            'users': DashboardStatistics.get_user_statistics(),
            'shops': DashboardStatistics.get_shop_statistics(),
            'products': DashboardStatistics.get_product_statistics(),
            'deliveries': DashboardStatistics.get_delivery_statistics(),
            'bookings': DashboardStatistics.get_booking_statistics(),
            'events': DashboardStatistics.get_event_statistics(),
            'tickets': DashboardStatistics.get_ticket_statistics(),
        }

# ============================================
# TIME-BASED QUERIES
# ============================================

class TimeBasedQueries:
    """Generate time-based statistics"""
    
    @staticmethod
    def get_last_7_days_stats():
        """Get statistics for last 7 days"""
        last_7_days = timezone.now() - timedelta(days=7)
        
        return {
            'new_users': User.objects.filter(date_joined__gte=last_7_days).count(),
            'new_shops': Shop.objects.filter(created_at__gte=last_7_days).count(),
            'new_products': Product.objects.filter(created_at__gte=last_7_days).count(),
            'new_bookings': Booking.objects.filter(created_at__gte=last_7_days).count(),
            'new_events': Event.objects.filter(created_at__gte=last_7_days).count(),
        }
    
    @staticmethod
    def get_last_30_days_stats():
        """Get statistics for last 30 days"""
        last_30_days = timezone.now() - timedelta(days=30)
        
        return {
            'new_users': User.objects.filter(date_joined__gte=last_30_days).count(),
            'new_shops': Shop.objects.filter(created_at__gte=last_30_days).count(),
            'new_products': Product.objects.filter(created_at__gte=last_30_days).count(),
            'deliveries_completed': Delivery.objects.filter(
                delivered_at__gte=last_30_days,
                status='delivered'
            ).count(),
            'bookings_completed': Booking.objects.filter(
                updated_at__gte=last_30_days,
                booking_status='checked_out'
            ).count(),
        }

# ============================================
# APPROVAL WORKFLOWS
# ============================================

class ApprovalWorkflow:
    """Handle approval workflows"""
    
    @staticmethod
    def get_pending_approvals():
        """Get all pending approvals"""
        return {
            'shops': Shop.objects.filter(status='pending').count(),
            'properties': Property.objects.filter(
                is_publicly_visible=False).count(),
            'lodges': Lodge.objects.filter(is_verified=False).count(),
        }
    
    @staticmethod
    def get_approval_queue():
        """Get items in approval queue"""
        return {
            'shops': list(Shop.objects.filter(
                status='pending'
            ).values('id', 'name', 'owner__username', 'created_at')[:10]),
            'properties': list(Property.objects.filter(
                is_publicly_visible=False
            ).values('id', 'title', 'owner__username', 'created_at')[:10]),
            'lodges': list(Lodge.objects.filter(
                is_verified=False
            ).values('id', 'name', 'owner__username', 'created_at')[:10]),
        }
    
    @staticmethod
    def bulk_approve(model_name, ids):
        """Bulk approve items"""
        if model_name == 'shops':
            Shop.objects.filter(id__in=ids).update(status='approved')
            return len(ids)
        elif model_name == 'lodges':
            Lodge.objects.filter(id__in=ids).update(is_verified=True)
            return len(ids)
        return 0

# ============================================
# SEARCH & FILTER HELPERS
# ============================================

class SearchFilters:
    """Common search and filter operations"""
    
    @staticmethod
    def search_users(query):
        """Search users by multiple fields"""
        return User.objects.filter(
            Q(username__icontains=query) |
            Q(email__icontains=query) |
            Q(phone_number__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query)
        )
    
    @staticmethod
    def search_shops(query):
        """Search shops"""
        return Shop.objects.filter(
            Q(name__icontains=query) |
            Q(owner__username__icontains=query) |
            Q(category__icontains=query) |
            Q(city__icontains=query)
        )
    
    @staticmethod
    def search_products(query):
        """Search products"""
        return Product.objects.filter(
            Q(name__icontains=query) |
            Q(sku__icontains=query) |
            Q(category__icontains=query)
        )
    
    @staticmethod
    def search_properties(query):
        """Search properties"""
        return Property.objects.filter(
            Q(title__icontains=query) |
            Q(address__icontains=query) |
            Q(city__icontains=query) |
            Q(owner__username__icontains=query)
        )

# ============================================
# PAGINATION HELPER
# ============================================

class PaginationHelper:
    """Handle pagination"""
    
    @staticmethod
    def paginate_queryset(queryset, page=1, per_page=20):
        """Paginate a queryset"""
        total = queryset.count()
        start = (page - 1) * per_page
        end = start + per_page
        
        items = queryset[start:end]
        total_pages = (total + per_page - 1) // per_page
        
        return {
            'items': items,
            'page': page,
            'per_page': per_page,
            'total': total,
            'total_pages': total_pages,
            'has_next': page < total_pages,
            'has_prev': page > 1,
        }

# ============================================
# AUDIT LOG HELPER
# ============================================

class AuditLog:
    """Log admin actions (optional - implement with your logging system)"""
    
    @staticmethod
    def log_action(user, action, model, object_id, details=''):
        """
        Log an admin action
        Implement with your preferred logging system (database, file, etc.)
        """
        log_message = f"[{datetime.now().isoformat()}] Admin: {user.username} | Action: {action} | Model: {model} | ID: {object_id} | Details: {details}"
        # TODO: Save to your logging system
        print(log_message)
    
    @staticmethod
    def log_approval(user, model, object_id, status):
        """Log approval actions"""
        AuditLog.log_action(
            user=user,
            action=f'approve_{status}',
            model=model,
            object_id=object_id,
            details=f'Status changed to {status}'
        )

# ============================================
# VALIDATION HELPERS
# ============================================

class ValidationHelpers:
    """Validation utilities"""
    
    @staticmethod
    def validate_user_action(user, action):
        """Validate user-specific actions"""
        valid_actions = ['verify', 'suspend', 'activate']
        return action in valid_actions
    
    @staticmethod
    def validate_shop_action(shop, action):
        """Validate shop-specific actions"""
        valid_actions = ['approve', 'reject', 'suspend', 'activate']
        return action in valid_actions
    
    @staticmethod
    def validate_property_action(property_obj, action):
        """Validate property-specific actions"""
        valid_actions = ['approve', 'reject']
        return action in valid_actions
    
    @staticmethod
    def validate_booking_action(booking, action):
        """Validate booking-specific actions"""
        valid_actions = ['confirm', 'cancel', 'check_in', 'check_out']
        # Add business logic checks
        if action == 'check_in' and booking.booking_status != 'confirmed':
            return False
        return action in valid_actions

# ============================================
# EXPORT HELPERS
# ============================================

import csv
from django.http import HttpResponse

class ExportHelpers:
    """Export data in various formats"""
    
    @staticmethod
    def export_to_csv(queryset, fields, filename):
        """Export queryset to CSV"""
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        writer = csv.writer(response)
        writer.writerow(fields)
        
        for obj in queryset:
            writer.writerow([getattr(obj, field) for field in fields])
        
        return response
    
    @staticmethod
    def export_users_csv(queryset):
        """Export users to CSV"""
        fields = ['username', 'email', 'phone_number', 'user_type', 'is_verified', 'date_joined']
        return ExportHelpers.export_to_csv(queryset, fields, 'users_export.csv')
    
    @staticmethod
    def export_shops_csv(queryset):
        """Export shops to CSV"""
        fields = ['name', 'owner', 'status', 'rating', 'created_at']
        return ExportHelpers.export_to_csv(queryset, fields, 'shops_export.csv')

# ============================================
# EMAIL NOTIFICATION HELPERS
# ============================================

from django.core.mail import send_mail
from django.template.loader import render_to_string

class NotificationHelpers:
    """Send notifications to users"""
    
    @staticmethod
    def notify_shop_approval(shop):
        """Notify shop owner of approval"""
        subject = f'Your shop "{shop.name}" has been approved!'
        message = f'Congratulations! Your shop has been approved and is now live.'
        send_mail(subject, message, 'noreply@marketplace.com', [shop.owner.email])
    
    @staticmethod
    def notify_shop_rejection(shop):
        """Notify shop owner of rejection"""
        subject = f'Your shop "{shop.name}" application status'
        message = f'Unfortunately, your shop application was not approved. Please contact support for more details.'
        send_mail(subject, message, 'noreply@marketplace.com', [shop.owner.email])
    
    @staticmethod
    def notify_lodge_verification(lodge):
        """Notify lodge owner of verification"""
        subject = f'Your lodge "{lodge.name}" has been verified!'
        message = f'Congratulations! Your lodge has been verified and is visible to customers.'
        send_mail(subject, message, 'noreply@marketplace.com', [lodge.owner.email])