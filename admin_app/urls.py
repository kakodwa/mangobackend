from django.urls import path
from . import views as admin_views
from .views import AdminLoginView, admin_logout,AdminDashboardView, ProcessWithdrawalActionView

urlpatterns = [
    
    path('admin_login/', AdminLoginView.as_view(), name='admin_login'),
    path('admin-portal/logout/', admin_logout, name='admin_logout'),

    path('-console/dashboard/', AdminDashboardView.as_view(), name='admin_dashboard'),
    path('console/withdrawals/<int:pk>/<str:action_type>/', ProcessWithdrawalActionView.as_view(), name='process_withdrawal'),
]




