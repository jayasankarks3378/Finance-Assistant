from django.shortcuts import render, redirect, get_object_or_404, HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib import messages
from django.conf import settings
from django.db.models import Sum
from django.core.paginator import Paginator
from django.db.models import Sum

from .models import Income, Expense
from .forms import IncomeForm, ExpenseForm, BillUploadForm

import os,csv,cv2,pytesseract,json,numpy as np
from datetime import datetime
from dotenv import load_dotenv
from groq import Groq



# Load environment variables
load_dotenv()
pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_CMD

# Initialize Groq client
GROQ_API_KEY = os.getenv('GROQ_API_KEY')
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY environment variable is not set")
    
groq_client = Groq(api_key=GROQ_API_KEY)  

@login_required
def upload_bill(request):
    if request.method == 'POST':
        form = BillUploadForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                # Associate bill with user
                bill = form.save(commit=False)
                bill.user = request.user
                bill.save()

                # Process the image
                file_path = os.path.join(settings.MEDIA_ROOT, str(bill.file))
                processed_image = process_bill_image(file_path)
                text_content = extract_text(processed_image)
                
                if text_content:
                    # Extract data using Groq
                    extracted_data = ai_extract(text_content)
                    print(extracted_data)
                    
                    if extracted_data:
                        # Create expense entry
                        expense = Expense.objects.create(
                            user=request.user,
                            amount=float(extracted_data['total']) / 100,  # Convert pennies to pounds
                            description=f"{extracted_data['business']}",
                            date=datetime.strptime(extracted_data['date'], '%Y-%m-%d').date() if 'date' in extracted_data else datetime.now().date()
                        )
                        
                        # Mark bill as processed
                        bill.processed = True
                        bill.save()
                        
                        messages.success(request, 'Bill processed successfully!')
                        return redirect('finances:dashboard')
                    else:
                        messages.warning(request, 'Could not extract information from the bill. Please add expense manually.')
                
            except Exception as e:
                messages.error(request, f'Error processing bill: {str(e)}')
                return redirect('finances:dashboard')
    else:
        form = BillUploadForm()

    return render(request, 'finances/upload_bill.html', {'form': form})

def process_bill_image(file_path):
    image = cv2.imread(file_path)
    # Denoising
    image = cv2.fastNlMeansDenoisingColored(image, None, 10, 10, 7, 21)
    # Upscaling (2x) using cubic interpolation
    height, width = image.shape[:2]
    image = cv2.resize(image, (width * 2, height * 2), interpolation=cv2.INTER_CUBIC)
    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    # Sharpening kernel
    kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
    sharpened = cv2.filter2D(gray, -1, kernel)
    # Binarization using OTSU thresholding
    _, threshold = cv2.threshold(sharpened, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return threshold

def extract_text(image):
    return pytesseract.image_to_string(image)

def ai_extract(text_content):
    prompt = """You are a receipt parser AI. Extract only these details from the receipt:
    1. Total amount (in pennies)
    2. Business/store name
    3. Date (in YYYY-MM-DD format)
    
    Return ONLY a JSON object with this structure:
    {
        "total": number,
        "business": string,
        "date": string
    }
    
    Here is the receipt text: """ + text_content

    try:
        response = groq_client.chat.completions.create(
            model="mixtral-8x7b-32768",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.1,
            max_tokens=500
        )
        
        # Extract and parse JSON response
        
        response_text = response.choices[0].message.content
        json_start = response_text.find('{')
        json_end = response_text.rfind('}') + 1
        
        if json_start >= 0 and json_end > json_start:
            json_str = response_text[json_start:json_end]
            return json.loads(json_str)
        return None
        
    except Exception as e:
        print(f"Error in Groq API processing: {str(e)}")
        return None


@login_required
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



def home(request):
    return render(request, 'finances/home.html')

# @login_required
# def dashboard(request):
#     incomes = Income.objects.filter(user=request.user)
#     expenses = Expense.objects.filter(user=request.user)
#     total_income = incomes.aggregate(Sum('amount'))['amount__sum'] or 0
#     total_expenses = expenses.aggregate(Sum('amount'))['amount__sum'] or 0
#     balance = total_income - total_expenses
#     search_date = request.GET.get('date')
#     user = request.user
#     if not user.is_authenticated:
#         return render(request, 'finances/dashboard.html', {'expenses': []})
#     expenses = Expense.objects.filter(user=user)
#     if search_date:
#         expenses = expenses.filter(date=search_date)
#     return render(request, 'finances/dashboard.html', {
#         'incomes': incomes,
#         'expenses': expenses,
#         'total_income': total_income,
#         'total_expenses': total_expenses,
#         'balance': balance,
#         'search_date': search_date, 
#     })
from datetime import datetime
from dateutil.relativedelta import relativedelta
from django.db.models.functions import TruncMonth

@login_required
def dashboard(request):
    total_income = Income.objects.filter(user=request.user).aggregate(Sum('amount'))['amount__sum'] or 0
    total_expenses = Expense.objects.filter(user=request.user).aggregate(Sum('amount'))['amount__sum'] or 0
    balance = total_income - total_expenses
    income_years = Income.objects.filter(user=request.user).dates('date', 'year', order='DESC')
    expense_years = Expense.objects.filter(user=request.user).dates('date', 'year', order='DESC')

    month = request.GET.get('month')
    year = request.GET.get('year')
    date = request.GET.get('date')

    try:
        month = int(month) if month else None
        year = int(year) if year else None
    except ValueError:
        month = None
        year = None

    expenses = Expense.objects.filter(user=request.user)
    
    if month and year:
        expenses = expenses.filter(date__month=month, date__year=year)
    elif month:
        expenses = expenses.filter(date__month=month)
    elif year:
        expenses = expenses.filter(date__year=year)
    if date:
        expenses = expenses.filter(date=date)

    # Fix "None" issue in expenses by ensuring month_year is set correctly
    expense_data = {}
    for expense in expenses:
        if expense.date:
            key = expense.date.strftime("%B %Y")
        else:
            key = "Unknown Date"

        if key not in expense_data:
            expense_data[key] = {'total': 0, 'list': []}
        expense_data[key]['total'] += expense.amount
        expense_data[key]['list'].append(expense)

    available_years = sorted(set(
        y.year for y in Income.objects.filter(user=request.user).dates('date', 'year', order='DESC')
    ) | set(
        y.year for y in Expense.objects.filter(user=request.user).dates('date', 'year', order='DESC')
    ), reverse=True)

    # Pagination: Show 7 expenses per page (example)
    paginator = Paginator(expenses, 7)  
    page_number = request.GET.get('page')
    expenses_page = paginator.get_page(page_number)

    # Get data for chart - last 12 months
    current_date = datetime.now()
    
    # Prepare chart data
    chart_data = {}
    
    # Get last 12 months
    for i in range(11, -1, -1):
        month_date = current_date - relativedelta(months=i)
        month_name = month_date.strftime("%b %Y")
        chart_data[month_name] = {'income': 0, 'expense': 0}
    
    # Calculate income for each month
    monthly_incomes = Income.objects.filter(
        user=request.user,
        date__gte=current_date - relativedelta(months=12)
    ).annotate(
        month=TruncMonth('date')
    ).values('month').annotate(
        total=Sum('amount')
    ).order_by('month')
    
    for income in monthly_incomes:
        month_name = income['month'].strftime("%b %Y")
        if month_name in chart_data:
            chart_data[month_name]['income'] = float(income['total'])
    
    # Calculate expenses for each month
    monthly_expenses = Expense.objects.filter(
        user=request.user,
        date__gte=current_date - relativedelta(months=12)
    ).annotate(
        month=TruncMonth('date')
    ).values('month').annotate(
        total=Sum('amount')
    ).order_by('month')
    
    for expense in monthly_expenses:
        month_name = expense['month'].strftime("%b %Y")
        if month_name in chart_data:
            chart_data[month_name]['expense'] = float(expense['total'])
    
    # Convert to lists for the chart
    chart_labels = list(chart_data.keys())
    chart_income = [chart_data[month]['income'] for month in chart_labels]
    chart_expenses = [chart_data[month]['expense'] for month in chart_labels]

    context = {
        "total_income": total_income,
        "total_expenses": total_expenses,
        "balance": balance,
        "incomes": Income.objects.filter(user=request.user),
        "expenses": expenses_page,
        "expense_list": [{'grouper': k, 'total': v['total'], 'list': v['list']} for k, v in expense_data.items()],
        "available_months": range(1, 13),   
        "available_years": available_years,
        "chart_labels": chart_labels,
        "chart_income": chart_income,
        "chart_expenses": chart_expenses,
    }
    
    return render(request, "finances/dashboard.html", context)

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
