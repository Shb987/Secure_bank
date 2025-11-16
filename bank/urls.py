from django.urls import path
from . import views
from django.shortcuts import render

urlpatterns = [
    # Home
    path('', lambda request: render(request, 'base2.html'), name='home'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),

    # User Dashboard
    path('dashboard/', views.user_dashboard, name='user_dashboard'),
    path('apply-loan/', views.apply_loan, name='apply_loan'),
    path('my-loans/', views.user_loan_list, name='user_loans'),
    path("profile/", views.user_profile, name="user_profile"),
    

    # Admin Panel
    path('admin-panel/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-panel/users/', views.admin_user_list, name='admin_users'),  # or user_management
    path('admin-panel/users/<int:user_id>/', views.admin_user_details, name='admin_user_detail'),
    path('admin-panel/users/<int:user_id>/delete/', views.admin_user_delete, name='admin_user_delete'),
    path('admin-panel/users/<int:user_id>/', views.admin_user_details, name='admin_user_details'),

    path('admin-panel/loans/', views.loan_list, name='loan_list'),  # or loan_management
    path('admin-panel/loans/approved/', views.approved_loans, name='loans_approved'),
    path('admin-panel/loans/<int:loan_id>/', views.loan_detail, name='loan_details'),

    path('admin-panel/loans/<int:loan_id>/approve/', views.approve_loan, name='approve_loan'),
    path('admin-panel/loans/<int:loan_id>/reject/', views.reject_loan, name='reject_loan'),
    path('admin-panel/loans/<int:loan_id>/pending/', views.pending_loan, name='pending_loan'),

    path('admin-panel/loans/<int:loan_id>/update_status/', views.update_loan_status, name='update_loan_status'),

    # Loan Applications (user side?)
    path('loan-applications/', views.loan_applications, name='loan_applications'),
    path('loan-applications/new/', views.loan_application_form, name='loan_application_form'),
    path('loan-applications/submit/', views.loan_application_submit, name='loan_application_submit'),
]
