from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from allauth.socialaccount.models import SocialAccount

from core.managers import ManageEmployees
from core.utils import Utils
from core.models import Employee
# Create your views here.

def login(request):
    if request.method == 'POST':
        # Get the credentials from the form
        name = request.POST.get('name')
        password = request.POST.get('password')
        
        # Verify credentials against SQL database
        
        if Utils.ValidateEmployeeLogin(name, password):
            # Get employee details to store role in session
            try:
                employee = Employee.objects.get(name=name, password=password)
                request.session['employee_id'] = employee.id
                request.session['employee_name'] = employee.name
                request.session['employee_role'] = employee.role
                request.session['is_oauth'] = False
            except Employee.DoesNotExist:
                pass
            
            # Credentials are valid, redirect to home page
            return redirect('home')
        else:
            # Invalid credentials, show error message
            messages.error(request, 'Invalid name or password.')
            return redirect('login')

    return render(request, 'homePage/login.html')


def home(request):
    # Explicitly force terminal selector when requested
    if request.GET.get('force_select') == '1':
        return render(request, 'homePage/index.html', {
            'is_manager': False,
            'employee_role': request.session.get('employee_role'),
            'is_oauth': request.session.get('is_oauth', False),
        })
    # Check if user is authenticated via Django's auth system (OAuth)
    if request.user.is_authenticated:
        # Check if this is a social account (OAuth login)
        try:
            social_account = SocialAccount.objects.filter(user=request.user).first()
            if social_account:
                # User logged in via Google OAuth - redirect to kiosk
                request.session['is_oauth'] = True
                request.session['employee_role'] = None
                return redirect('customer_kiosk:home')
        except Exception:
            pass
    
    # Check if user logged in via OAuth (from session)
    is_oauth = request.session.get('is_oauth', False)
    
    # Get employee role from session
    employee_role = request.session.get('employee_role', None)
    
    # Check if user is a manager (case-insensitive comparison)
    is_manager = False
    if employee_role and employee_role.lower() == 'manager':
        is_manager = True
    
    context = {
        'is_manager': is_manager,
        'employee_role': employee_role,
        'is_oauth': is_oauth
    }

    if is_manager:    
        return render(request, 'homePage/index.html', context)
    else:
        return redirect('cashier:home')
