from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.models import User
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from .models import LoanRequest
from .forms import LoanRequestForm, CustomUserCreationForm

import joblib
import numpy as np

# -------------------- ML MODEL LOADING --------------------
Rf_model = joblib.load('ml_models/rf_model.pkl')
scaler_loaded = joblib.load("ml_models/minmax_scaler.pkl")

# -------------------- HELPER FUNCTIONS --------------------
def is_admin(user):
    return user.is_staff

# -------------------- USER VIEWS --------------------
def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('admin_dashboard' if user.is_staff else 'user_dashboard')
        else:
            return render(request, 'base2.html', {'error': 'Invalid credentials'})
    return render(request, 'base2.html')


@login_required
def user_dashboard(request):
    loans = LoanRequest.objects.filter(user=request.user)
    context = {
        "active_loans": loans.filter(status='Approved').count(),
        "pending_loans": loans.filter(status='Pending').count(),
        "rejected_loans": loans.filter(status='Rejected').count(),
        "full_name": request.user.get_full_name() or request.user.username,
        "active": "dashboard"
    }
    return render(request, "user/dashboard.html", context)


@login_required
def loan_applications(request):
    loans = LoanRequest.objects.filter(user=request.user)
    return render(request, "user/loan_applications.html", {
        "loan_applications": loans,
        "full_name": request.user.get_full_name() or request.user.username,
        "active": "loan_applications"
    })


@login_required
def loan_application_form(request):
    return render(request, "user/loan_form.html", {
        "full_name": request.user.get_full_name() or request.user.username,
        "active": "loan_applications"
    })


@login_required
@csrf_exempt
def loan_application_submit(request):
    if request.method != 'POST':
        return render(request, 'user/loan_form.html')

    try:
        # Step 1
        income_annum = float(request.POST.get('income_annum'))
        loan_amount = float(request.POST.get('loan_amount'))

        # Step 2
        no_of_dependents = int(request.POST.get('no_of_dependents'))
        education = 0 if request.POST.get('education') == "Graduate" else 1
        self_employed = 1 if request.POST.get('self_employed') == "Yes" else 0
        loan_term = int(request.POST.get('loan_term'))
        cibil_score = float(request.POST.get('cibil_score'))
        residential_assets_value = float(request.POST.get('residential_assets_value'))
        commercial_assets_value = float(request.POST.get('commercial_assets_value'))
        luxury_assets_value = float(request.POST.get('luxury_assets_value'))
        bank_asset_value = float(request.POST.get('bank_asset_value'))

        # Auto-calculated
        debt_to_income = loan_amount / income_annum if income_annum > 0 else 0

        # Prepare numeric array for scaling
        numeric_values = np.array([[no_of_dependents, loan_term, cibil_score,
                                    residential_assets_value, commercial_assets_value,
                                    luxury_assets_value, bank_asset_value, debt_to_income]])
        numeric_scaled = scaler_loaded.transform(numeric_values)

        # Insert categorical features
        features_final = np.insert(numeric_scaled, 1, education, axis=1)
        features_final = np.insert(features_final, 2, self_employed, axis=1)

        prediction = Rf_model.predict(features_final)[0]  # 1=Approved, 0=Rejected

        LoanRequest.objects.create(
            user=request.user,
            loan_type=request.POST.get('loan_type', 'personal'),
            amount=loan_amount,
            purpose="Loan Application",
            status='Approved' if prediction == 0 else 'Rejected'
        )

        if prediction == 1:
            messages.warning(request, "⚠ Loan application submitted but rejected.")
        else:
            messages.success(request, "✅ Loan application submitted & approved!")

    except Exception as e:
        print("Error saving loan:", e)
        messages.error(request, "❌ Failed to submit your loan application.")

    return redirect('loan_applications')


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
    loans = LoanRequest.objects.filter(user=request.user).order_by('-application_date')
    return render(request, 'user/loan_list.html', {
        'loans': loans,
        "full_name": request.user.get_full_name() or request.user.username,
        "active": "loan_list"
    })


@login_required
def user_profile(request):
    user = request.user

    if request.method == 'POST':
        if 'update_profile' in request.POST:
            user.first_name = request.POST.get('first_name', user.first_name)
            user.last_name = request.POST.get('last_name', user.last_name)
            user.email = request.POST.get('email', user.email)
            user.save()
            messages.success(request, "Profile updated successfully!")

        elif 'change_password' in request.POST:
            old_password = request.POST.get('old_password')
            new_password1 = request.POST.get('new_password1')
            new_password2 = request.POST.get('new_password2')

            if not user.check_password(old_password):
                messages.error(request, "Current password is incorrect.")
            elif new_password1 != new_password2:
                messages.error(request, "New passwords do not match.")
            else:
                user.set_password(new_password1)
                user.save()
                update_session_auth_hash(request, user)
                messages.success(request, "Password changed successfully!")

    return render(request, "user/user_profile.html", {
        "user": user,
        "active": "profile",
        "full_name": request.user.get_full_name() or request.user.username
    })


def logout_view(request):
    logout(request)
    return redirect('login')


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

# -------------------- ADMIN VIEWS --------------------
@user_passes_test(is_admin)
def admin_dashboard(request):
    context = {
        'total_users': User.objects.filter(is_staff=False).count(),
        'total_loans': LoanRequest.objects.all().count(),
        'approved_loans': LoanRequest.objects.filter(status='Approved').count(),
        'pending_loans': LoanRequest.objects.filter(status='Pending').count(),
        'users': User.objects.filter(is_staff=False).order_by('-date_joined'),
        'loan_applications': LoanRequest.objects.select_related('user').order_by('-application_date')[:50],
        'recent_activities': LoanRequest.objects.select_related('user').order_by('-application_date')[:5]
    }
    return render(request, 'admin_panel/dashboard.html', context)


@user_passes_test(is_admin)
def admin_user_list(request):
    users = User.objects.filter(is_staff=False).order_by('-date_joined')
    return render(request, 'admin_panel/users.html', {'users': users})


@user_passes_test(is_admin)
def admin_user_details(request, user_id):
    user = get_object_or_404(User, id=user_id)
    user_loans = LoanRequest.objects.filter(user=user).order_by('-application_date')
    return render(request, 'admin_panel/user_details.html', {'user': user, 'user_loans': user_loans})


@user_passes_test(is_admin)
def admin_user_delete(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if not user.is_staff:
        user.delete()
    return redirect('admin_users')


@user_passes_test(is_admin)
def loan_list(request):
    loans = LoanRequest.objects.select_related('user').order_by('-application_date')
    return render(request, 'admin_panel/loans.html', {'loans': loans})


@user_passes_test(is_admin)
def loan_detail(request, loan_id):
    loan = get_object_or_404(LoanRequest, id=loan_id)
    return render(request, 'admin_panel/loan_details.html', {'loan': loan})


@user_passes_test(is_admin)
def user_management(request):
    users = User.objects.filter(is_staff=False).order_by("-date_joined")
    return render(request, "admin_panel/user_management.html", {"users": users})


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
def pending_loan(request, loan_id):
    loan = get_object_or_404(LoanRequest, id=loan_id)
    loan.status = 'Pending'
    loan.save()
    return redirect('loan_list')


@user_passes_test(is_admin)
def approved_loans(request):
    loans = LoanRequest.objects.filter(status='Approved').select_related('user').order_by('-application_date')
    return render(request, 'admin_panel/loans_approved.html', {'loans': loans})


@login_required
@user_passes_test(is_admin)
def update_loan_status(request, loan_id):
    if request.method == 'POST':
        loan = get_object_or_404(LoanRequest, id=loan_id)
        new_status = request.POST.get('status')
        loan.status = new_status
        loan.save()
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
