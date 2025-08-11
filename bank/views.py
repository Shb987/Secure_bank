from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import LoanRequest
from django.contrib.auth.models import User
from .forms import LoanRequestForm


def is_admin(user):
    return user.is_staff


# ------------------- USER VIEWS -------------------
from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            if user.is_staff:
                return redirect('admin_dashboard')
            else:
                return redirect('user_dashboard')
        else:
            return render(request, 'base2.html', {'error': 'Invalid credentials'})
    return render(request, 'base2.html')

# def user_dashboard(request):
#     user_loans = LoanRequest.objects.filter(user=request.user)

#     context = {
#         'active_loans': user_loans.filter(status='approved').count(),
#         'pending_loans': user_loans.filter(status='pending').count(),
#         'rejected_loans': user_loans.filter(status='rejected').count(),
#         'total_loans': user_loans.count(),
#         'full_name': request.user.get_full_name() or request.user.username,
#         'loan_applications': user_loans.order_by('-application_date')  # latest first

#     }
#     print(context)
#     return render(request, 'user/db2.html', context)

def user_dashboard(request):
    loans = LoanRequest.objects.filter(user=request.user)
    return render(request, "user/dashboard.html", {
        "active_loans": loans.filter(status='approved').count(),
        "pending_loans": loans.filter(status='pending').count(),
        "rejected_loans": loans.filter(status='rejected').count(),
        "full_name": request.user.get_full_name() or request.user.username,
        "active": "dashboard"
    })

def loan_applications(request):
    loans = LoanRequest.objects.filter(user=request.user)
    return render(request, "user/loan_applications.html", {
        "loan_applications": loans,
        "full_name": request.user.get_full_name() or request.user.username,
        "active": "loans"
    })

def loan_application_form(request):
    return render(request, "user/loan_form.html", {
        "full_name": request.user.get_full_name() or request.user.username,
        "active": "loans"
    })


import joblib
import pandas as pd
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import LoanRequest
from django.views.decorators.csrf import csrf_exempt
import numpy as np
# Load the trained RandomForest model (you save it after training)
Rf_model = joblib.load('ml_models/rf_model.pkl')
scaler_loaded = joblib.load("ml_models/minmax_scaler.pkl")

@login_required
@csrf_exempt
def loan_application_submit(request):
    if request.method == 'POST':
        try:
            # Step 1 values
            income_annum = float(request.POST.get('income_annum'))
            loan_amount = float(request.POST.get('loan_amount'))

            # Step 2 values
            no_of_dependents = int(request.POST.get('no_of_dependents'))
            education = 0 if request.POST.get('education') == "Graduate" else 1
            self_employed = 1 if request.POST.get('self_employed') == "Yes" else 0
            loan_term = int(request.POST.get('loan_term'))
            cibil_score = float(request.POST.get('cibil_score'))
            residential_assets_value = float(request.POST.get('residential_assets_value'))
            commercial_assets_value = float(request.POST.get('commercial_assets_value'))
            luxury_assets_value = float(request.POST.get('luxury_assets_value'))
            bank_asset_value = float(request.POST.get('bank_asset_value'))
            numerical_col = [no_of_dependents, loan_term, 'cibil_score',
                            'residential_assets_value', 'commercial_assets_value',
                            'luxury_assets_value', 'bank_asset_value', 'debt_to_income']
            # Auto-calculated
            debt_to_income = loan_amount / income_annum if income_annum > 0 else 0
            # Scale only numeric columns
            numeric_values = np.array([[
                no_of_dependents, loan_term, cibil_score,
                residential_assets_value, commercial_assets_value,
                luxury_assets_value, bank_asset_value, debt_to_income
            ]])
            numeric_scaled = scaler_loaded.transform(numeric_values)

            # Insert education & self_employed back in correct positions
            # Position 0 = scaled no_of_dependents
            # Position 1 = education (raw)
            # Position 2 = self_employed (raw)
            features_final = np.insert(numeric_scaled, 1, education, axis=1)  # insert education at index 1
            features_final = np.insert(features_final, 2, self_employed, axis=1)  # insert self_employed at index 2
            print(features_final)
            prediction = Rf_model.predict(features_final)[0]  # 1=Approved, 0=Rejected

            print(prediction)
            # Save LoanRequest (only valid model fields)
            LoanRequest.objects.create(
                user=request.user,
                loan_type=request.POST.get('loan_type', 'personal'),
                amount=loan_amount,
                purpose="Loan Application",  # Or capture actual purpose from form
                status='approved' if prediction == 1 else 'rejected'
            )

            # Success message
            if prediction == 1:
                messages.success(request, "✅ Loan application submitted & approved!")
            else:
                messages.warning(request, "⚠ Loan application submitted but rejected.")

        except Exception as e:
            print("Error saving loan:", e)
            messages.error(request, "❌ Failed to submit your loan application.")

        return redirect('loan_applications')  # Redirect to loan list page

    # If GET request, show form
    return render(request, 'user/loan_form.html')

# def loan_application_submit(request):
#     if request.method == 'POST':
#         # Step 1 data
#         income_annum = float(request.POST.get('income_annum'))
#         loan_amount = float(request.POST.get('loan_amount'))

#         # Step 2 data
#         no_of_dependents = int(request.POST.get('no_of_dependents'))
#         education = 1 if request.POST.get('education') == "Graduate" else 0
#         self_employed = 1 if request.POST.get('self_employed') == "Yes" else 0
#         loan_term = int(request.POST.get('loan_term'))
#         cibil_score = float(request.POST.get('cibil_score'))
#         residential_assets_value = float(request.POST.get('residential_assets_value'))
#         commercial_assets_value = float(request.POST.get('commercial_assets_value'))
#         luxury_assets_value = float(request.POST.get('luxury_assets_value'))
#         bank_asset_value = float(request.POST.get('bank_asset_value'))

#         # Auto-calculated field
#         debt_to_income = loan_amount / income_annum

#         # ML model prediction
#         features = np.array([[
#             no_of_dependents, education, self_employed, loan_term,
#             cibil_score, residential_assets_value, commercial_assets_value,
#             luxury_assets_value, bank_asset_value, debt_to_income
#         ]])

#         prediction = Rf_model.predict(features)[0]  # 1=Approved, 0=Rejected

#         # Save only the fields that exist in LoanRequest model
#         LoanRequest.objects.create(
#             user=request.user,
#             amount=loan_amount,  # matches the model field `amount`
#             term_months=loan_term,
#             status='approved' if prediction == 1 else 'rejected',
#             loan_type='personal',  # or get from form if needed
#             purpose="Loan application submitted via ML model",  # generic purpose
#             interest_rate=5.0
#         )

#         # Success or failure message
#         if prediction == 1:
#             messages.success(request, "✅ Your loan application has been approved!")
#         else:
#             messages.warning(request, "❌ Your loan application has been rejected.")

#         return render(request, 'user/db2.html')  # stay on same page

#     return render(request, 'user/db2.html')


@login_required
def apply_loan(request):
    if request.method == 'POST':
        form = LoanRequestForm(request.POST)
        if form.is_valid():
            loan = form.save(commit=False)
            loan.user = request.user
            loan.save()
            return redirect('user_loans')
    else:
        form = LoanRequestForm()
    return render(request, 'user/loan_request.html', {'form': form})


@login_required
def user_loan_list(request):
    loans = LoanRequest.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'user/loan_list.html', {'loans': loans})

def logout_view(request):
    logout(request)
    return redirect('login')
# ------------------- ADMIN VIEWS -------------------

@user_passes_test(is_admin)
def admin_dashboard(request):
    context = {
        'total_users': User.objects.filter(is_staff=False).count(),
        'total_loans': LoanRequest.objects.all().count(),
        'approved_loans': LoanRequest.objects.filter(status='Approved').count(),
        'pending_loans': LoanRequest.objects.filter(status='Pending').count(),
        'users' : User.objects.filter(is_staff=False).order_by('-date_joined'),
        'loan_applications': LoanRequest.objects.select_related('user').order_by('-application_date')[:50]

    }
    print(context)
    return render(request, 'admin_panel/dashboard2.html', context)


@user_passes_test(is_admin)
def admin_user_list(request):
    users = User.objects.filter(is_staff=True).order_by('-date_joined')
    return render(request, 'admin_panel/users.html', {'users': users})


@user_passes_test(is_admin)
def admin_user_detail(request, user_id):
    user = get_object_or_404(User, id=user_id)
    return render(request, 'admin_panel/user_detail.html', {'user': user})


@user_passes_test(is_admin)
def admin_user_delete(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if not user.is_staff:
        user.delete()
    return redirect('admin_users')

from django.contrib.auth.models import User
from django.contrib.auth import login
from .forms import CustomUserCreationForm
from django.contrib import messages

def register_view(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Account created successfully. Please log in.")
            return redirect("login")
    else:
        form = CustomUserCreationForm()
    return render(request, "register.html", {"form": form})

@user_passes_test(is_admin)
def loan_list(request):
    loans = LoanRequest.objects.select_related('user').order_by('-created_at')
    return render(request, 'admin_panel/loans.html', {'loans': loans})


@user_passes_test(is_admin)
def loan_detail(request, loan_id):
    loan = get_object_or_404(LoanRequest, id=loan_id)
    return render(request, 'admin_panel/loan_details.html', {'loan': loan})


@user_passes_test(is_admin)
def approve_loan(request, loan_id):
    loan = get_object_or_404(LoanRequest, id=loan_id)
    loan.status = 'Approved'
    loan.save()
    return redirect('loan_list')


@user_passes_test(is_admin)
def reject_loan(request, loan_id):
    loan = get_object_or_404(LoanRequest, id=loan_id)
    loan.status = 'Rejected'
    loan.save()
    return redirect('loan_list')


@user_passes_test(is_admin)
def approved_loans(request):
    loans = LoanRequest.objects.filter(status='Approved').select_related('user').order_by('-created_at')
    return render(request, 'admin_panel/loans_approved.html', {'loans': loans})


from django.shortcuts import redirect
from django.contrib.auth import logout

def logout_view(request):
    logout(request)
    return redirect('login')  # or redirect to your home page

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required

@login_required
@user_passes_test(is_admin)
def loan_detail(request, loan_id):
    print(loan_id)
    loan = get_object_or_404(LoanRequest, id=loan_id)
    print(loan)
    return render(request, 'admin_panel/detail.html', {'loan': loan})

@login_required
@user_passes_test(is_admin)
def update_loan_status(request, loan_id):
    if request.method == 'POST':
        loan = get_object_or_404(LoanRequest, id=loan_id)
        new_status = request.POST.get('status')
        loan.status = new_status
        loan.save()
        # Add status history record
        loan.status_history.create(status=new_status, changed_by=request.user)
        return redirect('loan_detail', loan_id=loan.id)
    return redirect('admin_dashboard')

@login_required
@user_passes_test(is_admin)
def save_loan_notes(request, loan_id):
    if request.method == 'POST':
        loan = get_object_or_404(LoanRequest, id=loan_id)
        loan.admin_notes = request.POST.get('notes', '')
        loan.save()
        return redirect('loan_detail', loan_id=loan.id)
    return redirect('admin_dashboard')