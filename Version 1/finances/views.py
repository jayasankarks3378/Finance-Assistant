# finances/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from .models import Income, Expense
from .forms import IncomeForm, ExpenseForm



# Signup View
def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=password)
            login(request, user)
            return redirect('finances:home')  # Redirect to dashboard after login
    else:
        form = UserCreationForm()
    return render(request, 'finances/signup.html', {'form': form})

# Login View
def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('finances:home')  # Redirect to dashboard after login
        else:
            return render(request, 'finances/login.html', {'error': 'Invalid credentials'})
    return render(request, 'finances/login.html')

# Logout View
def logout_view(request):
    logout(request)
    return redirect('finances:login')

# Dashboard View (only accessible to logged-in users)
@login_required
def dashboard(request):
    # Get income and expense records for the logged-in user
    incomes = Income.objects.filter(user=request.user)
    expenses = Expense.objects.filter(user=request.user)

    # Calculate totals
    total_income = incomes.aggregate(Sum('amount'))['amount__sum'] or 0
    total_expenses = expenses.aggregate(Sum('amount'))['amount__sum'] or 0
    balance = total_income - total_expenses

    # Pass the data to the template
    return render(request, 'finances/dashboard.html', {
        'incomes': incomes,
        'expenses': expenses,
        'total_income': total_income,
        'total_expenses': total_expenses,
        'balance': balance
    })

@login_required
def home(request):
    return render(request, 'finances/home.html')


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
# @login_required
# def add_expense(request):
#     if request.method == 'POST':
#         form = ExpenseForm(request.POST)
#         if form.is_valid():
#             form.instance.user = request.user  # Assign the logged-in user to the expense
#             form.save()
#             return redirect('finances/dashboard.html')
        
#         else:
#             print(form.errors)  # Add this line to inspect validation errors

#     else:
#         form = ExpenseForm()

#     return render(request, 'finances/add_expense.html', {'form': form})



@login_required
def add_expense(request):
    if request.method == 'POST':
        form = ExpenseForm(request.POST)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.user = request.user  # Assign the logged-in user to the expense
            expense.save()
            return redirect('finances:dashboard')  # Redirect to the dashboard after adding an expense
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
