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

def user_dashboard(request):
    user_loans = LoanRequest.objects.filter(user=request.user)

    context = {
        'active_loans': user_loans.filter(status='approved').count(),
        'pending_loans': user_loans.filter(status='pending').count(),
        'rejected_loans': user_loans.filter(status='rejected').count(),
        'total_loans': user_loans.count(),
        'full_name': request.user.get_full_name() or request.user.username,
        'loan_applications': user_loans.order_by('-application_date')  # latest first

    }
    print(context)
    return render(request, 'user/db2.html', context)


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