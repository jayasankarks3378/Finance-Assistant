# finances/views.py
from django.shortcuts import render, redirect, get_object_or_404,HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from .models import Income, Expense
from .forms import IncomeForm, ExpenseForm
import csv
from django.contrib import messages
import csv


def export_expenses(request):
    # Prepare the CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="expenses_report.csv"'
    
    # Create CSV writer
    writer = csv.writer(response)
    
    # Write comprehensive header
    writer.writerow([
        'User', 
        'Total Expenses', 
        'Expense Date', 
        'Amount', 
        'Description'
    ])
    
    # Get user's expenses with comprehensive details
    expenses = Expense.objects.filter(user=request.user).order_by('-date')
    
    # Calculate total expenses
    total_expenses = expenses.aggregate(Sum('amount'))['amount__sum'] or 0
    
    # Write summary row
    writer.writerow([
        request.user.username,
        f"Rs.{total_expenses:.2f}",
        "",  # Empty for summary row
        "",
        "Total Expenses"
    ])
    
    # Add a blank row for separation
    writer.writerow([])
    
    # Write individual expense details
    for expense in expenses:
        writer.writerow([
            request.user.username,
            "",  # Total moved to summary row
            expense.date.strftime('%Y-%m-%d'),
            f"Rs.{expense.amount:.2f}",
            expense.description
        ])
    
    return response

# Signup View
# finances/views.py
from django.shortcuts import render, redirect, get_object_or_404, HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.contrib import messages
from .models import Income, Expense
from .forms import IncomeForm, ExpenseForm
import csv

def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}!')
            user = authenticate(username=username, password=form.cleaned_data.get('password1'))
            if user is not None:
                login(request, user)
                return redirect('finances:dashboard')
        else:
            # Pass form errors to template
            return render(request, 'finances/signup.html', {'form': form})
    else:
        form = UserCreationForm()
    return render(request, 'finances/signup.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {username}!')
                return redirect('finances:dashboard')
            else:
                messages.error(request, 'Invalid username or password.')
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = AuthenticationForm()
    return render(request, 'finances/login.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('finances:home')

# ... rest of the existing views remain the same

def home(request):
    return render(request, 'finances/home.html')

@login_required
def dashboard(request):
    incomes = Income.objects.filter(user=request.user)
    expenses = Expense.objects.filter(user=request.user)
    total_income = incomes.aggregate(Sum('amount'))['amount__sum'] or 0
    total_expenses = expenses.aggregate(Sum('amount'))['amount__sum'] or 0
    balance = total_income - total_expenses
    search_date = request.GET.get('date')
    user = request.user
    if not user.is_authenticated:
        return render(request, 'finances/dashboard.html', {'expenses': []})
    expenses = Expense.objects.filter(user=user)
    if search_date:
        expenses = expenses.filter(date=search_date)
    return render(request, 'finances/dashboard.html', {
        'incomes': incomes,
        'expenses': expenses,
        'total_income': total_income,
        'total_expenses': total_expenses,
        'balance': balance,
        'search_date': search_date, 
    })


# Add Income
@login_required
def add_income(request):
    if request.method == 'POST':
        form = IncomeForm(request.POST)
        if form.is_valid():
            form.instance.user = request.user  # Assign the logged-in user to the income
            form.save()
            return redirect('finances:dashboard')
    else:
        form = IncomeForm()

    return render(request, 'finances/add_income.html', {'form': form})

# Add Expense
@login_required
def add_expense(request):
    if request.method == 'POST':
        form = ExpenseForm(request.POST)
        if form.is_valid():
            form.instance.user = request.user  
            form.save()
            return redirect('finances:dashboard')  
    else:
        form = ExpenseForm()

    return render(request, 'finances/add_expense.html', {'form': form})

# Edit Income
@login_required
def edit_income(request, income_id):
    income = get_object_or_404(Income, id=income_id, user=request.user)

    if request.method == 'POST':
        form = IncomeForm(request.POST, instance=income)
        if form.is_valid():
            form.save()
            return redirect('finances:dashboard')  # Redirect to the dashboard after saving
    else:
        form = IncomeForm(instance=income)

    return render(request, 'finances/edit_income.html', {'form': form})

# Edit Expense
@login_required
def edit_expense(request, expense_id):
    expense = get_object_or_404(Expense, id=expense_id, user=request.user)

    if request.method == 'POST':
        form = ExpenseForm(request.POST, instance=expense)
        if form.is_valid():
            form.save()
            return redirect('finances:dashboard')  # Redirect to the dashboard after saving
    else:
        form = ExpenseForm(instance=expense)

    return render(request, 'finances/edit_expense.html', {'form': form})

# Delete Income
@login_required
def delete_income(request, income_id):
    income = get_object_or_404(Income, id=income_id, user=request.user)
    income.delete()
    return redirect('finances:dashboard')

# Delete Expense
@login_required
def delete_expense(request, expense_id):
    expense = get_object_or_404(Expense, id=expense_id, user=request.user)
    expense.delete()
    return redirect('finances:dashboard')
