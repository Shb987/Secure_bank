from django.urls import path
from . import views
from django.shortcuts import render

urlpatterns = [
    # Home
    path('', lambda request: render(request, 'base2.html'), name='home'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),

    # Authentication
    path('dashboard/', views.user_dashboard, name='user_dashboard'),
    path('apply-loan/', views.apply_loan, name='apply_loan'),
    path('my-loans/', views.user_loan_list, name='user_loans'),

    # Admin Panel
    path('admin-panel/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-panel/users/', views.admin_user_list, name='admin_users'),
    path('admin-panel/users/<int:user_id>/', views.admin_user_detail, name='admin_user_detail'),
    path('admin-panel/users/<int:user_id>/delete/', views.admin_user_delete, name='admin_user_delete'),

    path('admin-panel/loans/', views.loan_list, name='loan_list'),
    path('admin-panel/loans/approved/', views.approved_loans, name='loans_approved'),
    path('admin-panel/loans/<int:loan_id>/', views.loan_detail, name='loan_detail'),
    path('admin-panel/loans/<int:loan_id>/approve/', views.approve_loan, name='approve_loan'),
    path('admin-panel/loans/<int:loan_id>/reject/', views.reject_loan, name='reject_loan'),
    path('admin-panel/loans/<int:loan_id>/', views.loan_detail, name='loan_detail'),
    path('admin-panel/loans/<int:loan_id>/update_status/', views.update_loan_status, name='update_loan_status'),
    # path('admin-panel/loans/<int:loan_id>/save_notes/', views.save_loan_notes, name='save_loan_notes'),
    # path('loans/', views.loan_management, name='loan_management'),
]
