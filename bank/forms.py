from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import LoanRequest, UserProfile


# ------------------------------
# Loan Request Form
# ------------------------------
class LoanRequestForm(forms.ModelForm):
    class Meta:
        model = LoanRequest
        fields = ['loan_type', 'amount', 'purpose', 'term_months']
        widgets = {
            'purpose': forms.Textarea(attrs={'rows': 3}),
        }


# ------------------------------
# User Profile Form
# ------------------------------
class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['address', 'phone', 'photo']
        widgets = {
            'address': forms.TextInput(attrs={
                "class": "w-full px-3 py-2 border rounded"
            }),
            'phone': forms.TextInput(attrs={
                "class": "w-full px-3 py-2 border rounded"
            }),
        }


# ------------------------------
# Custom User Signup Form
# ------------------------------
class CustomUserCreationForm(UserCreationForm):
    full_name = forms.CharField(
        max_length=150,
        required=True,
        label="Full Name",
        widget=forms.TextInput(attrs={
            "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary",
            "placeholder": "John Doe"
        })
    )

    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary",
            "placeholder": "you@example.com"
        })
    )

    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={
            "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary",
            "placeholder": ""
        })
    )

    password2 = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput(attrs={
            "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary",
            "placeholder": ""
        })
    )

    class Meta:
        model = User
        fields = ["full_name", "username", "email", "password1", "password2"]
        widgets = {
            "username": forms.TextInput(attrs={
                "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary",
                "placeholder": "username"
            })
        }

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Email already registered.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data["full_name"]
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user
