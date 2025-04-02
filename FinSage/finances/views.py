from django.shortcuts import render, redirect, get_object_or_404, HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib import messages
from django.conf import settings
from django.core.paginator import Paginator
from django.db import models
from django.db.models import Sum
from django.db.models.functions import TruncMonth
from django.contrib.auth.models import User
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import os, re, csv, cv2, pytesseract, json, numpy as np
from dotenv import load_dotenv
from groq import Groq

from .models import Income, Expense, FinancialAnalysis
from .forms import IncomeForm, ExpenseForm, BillUploadForm

groq_client = Groq(api_key='your_api_key')

@login_required
def financial_analysis_view(request):
    user = get_object_or_404(User, pk=request.user.pk)
    
    # Get user's financial data
    incomes = Income.objects.filter(user=user).order_by('-date')
    expenses = Expense.objects.filter(user=user).order_by('-date')
    
    # Get time period for analysis
    period = request.GET.get('period', 'all')
    analysis_type = request.GET.get('type', 'overview')
    
    # Filter data based on selected period
    if period == 'month':
        current_month = datetime.now().month
        current_year = datetime.now().year
        incomes = incomes.filter(date_month=current_month, date_year=current_year)
        expenses = expenses.filter(date_month=current_month, date_year=current_year)
        period_name = datetime.now().strftime('%B %Y')
    elif period == 'year':
        current_year = datetime.now().year
        incomes = incomes.filter(date__year=current_year)
        expenses = expenses.filter(date__year=current_year)
        period_name = str(current_year)
    else:
        period_name = 'All Time'
    
    # Prepare data for AI analysis
    total_income = incomes.aggregate(Sum('amount'))['amount__sum'] or 0
    total_expenses = expenses.aggregate(Sum('amount'))['amount__sum'] or 0
    balance = total_income - total_expenses
    savings_rate = (total_income - total_expenses) / total_income * 100 if total_income > 0 else 0
    
    # Group expenses by category - Fix for the 0 non-expression error
    expense_by_category = []
    if total_expenses > 0:  # Only perform this calculation if there are expenses
        expense_categories = expenses.values('category').annotate(total=Sum('amount')).order_by('-total')
        for category in expense_categories:
            percentage = (category['total'] / total_expenses) * 100 if total_expenses > 0 else 0
            expense_by_category.append({
                'category': category['category'] or 'Uncategorized',
                'total': float(category['total']),
                'percentage': float(percentage)
            })
    
    # Get recent transactions
    recent_transactions = list(expenses.values('date', 'amount', 'description', 'category')[:10])
    
    # Monthly breakdown
    monthly_data = expenses.annotate(
        month=TruncMonth('date')
    ).values('month').annotate(
        total=Sum('amount')
    ).order_by('-month')[:6]
    
    # Format data for analysis
    financial_data = {
        'period': period_name,
        'analysis_type': analysis_type,
        'total_income': float(total_income),
        'total_expenses': float(total_expenses),
        'balance': float(balance),
        'savings_rate': float(savings_rate),
        'expense_categories': expense_by_category,
        'recent_transactions': [
            {'date': transaction['date'].strftime('%Y-%m-%d'), 
             'amount': float(transaction['amount']), 
             'description': transaction['description'],
             'category': transaction['category'] or 'Uncategorized'} 
            for transaction in recent_transactions
        ],
        'monthly_trend': [
            {'month': item['month'].strftime('%b %Y'), 
             'amount': float(item['total'])} 
            for item in monthly_data
        ]
    }
    
    # Existing analysis check
    existing_analysis = None
    if period != 'all':
        try:
            existing_analysis = FinancialAnalysis.objects.filter(
                user=user,
                analysis_type=analysis_type,
                analysis_period=period_name
            ).first()
        except FinancialAnalysis.DoesNotExist:
            existing_analysis = None
    
    insights, recommendations = None, None
    if existing_analysis:
        insights = existing_analysis.insights
        recommendations = existing_analysis.recommendations
    else:
        # Generate insights using Groq API
        try:
            insights, recommendations = generate_ai_insights(financial_data)
            
            # Save analysis results
            if insights:
                FinancialAnalysis.objects.create(
                    user=user,
                    analysis_type=analysis_type,
                    analysis_period=period_name,
                    insights=insights,
                    recommendations=recommendations
                )
        except Exception as e:
            insights = f"Error generating insights: {str(e)}"
            recommendations = "Please try again later."
    
    # Process recommendations for better display
    processed_recommendations = []
    if recommendations:
        # Split by newlines or list markers
        raw_recommendations = re.split(r'\n\s*\n|\n-|\d+\.\s+', recommendations)
        for rec in raw_recommendations:
            if rec.strip():  # Check if not empty after stripping whitespace
                # Remove any stray list markers and clean up text
                cleaned_rec = re.sub(r'^[-•]\s', '', rec.strip())
                processed_recommendations.append(cleaned_rec)
    
    context = {
        'financial_data': financial_data,
        'insights': insights,
        'recommendations': processed_recommendations,
        'period': period,
        'analysis_type': analysis_type,
        "total_income": total_income,
        "total_expenses": total_expenses,
        "balance": balance,
    }
    
    return render(request, 'finances/analysis.html', context)

def generate_ai_insights(financial_data):
    """Generate financial insights using Groq API with improved formatting for insights and recommendations"""
    
    try:
        # Your existing prompt code remains the same
        prompt = f"""You are a financial advisor AI. Analyze the following financial data and provide:
        1. Insightful observations about spending patterns, savings, and financial health
        2. Specific, actionable recommendations that the user can implement immediately
        
        Financial data for period {financial_data['period']}:
        - Total Income: ₹{financial_data['total_income']:.2f}
        - Total Expenses: ₹{financial_data['total_expenses']:.2f}
        - Balance: ₹{financial_data['balance']:.2f}
        - Savings Rate: {financial_data['savings_rate']:.2f}%
        
        Expense Categories:
        {json.dumps(financial_data['expense_categories'], indent=2)}
        
        Recent Transactions:
        {json.dumps(financial_data['recent_transactions'], indent=2)}
        
        Monthly Spending Trend:
        {json.dumps(financial_data['monthly_trend'], indent=2)}
        
        Provide the response in this format:
        ---INSIGHTS---
        Achievement: [First insight title]
        [Write a meaningful insight with specific numbers from the data]
        
        Opportunity: [Second insight title]
        [Write a meaningful insight with specific numbers from the data]
        
        Warning: [Third insight title]
        [Write a meaningful insight with specific numbers from the data]
        
        [Add 1-2 more insights with clear titles if appropriate]
        
        ---RECOMMENDATIONS---
        1. [Specific, immediate action the user can take] - [Brief explanation why this matters]
        
        2. [Another specific, immediate action] - [Brief explanation with quantifiable benefit]
        
        3. [Another specific action with a timeframe] - [Explanation with expected outcome]
        
        [Add 1 more recommendation if appropriate]
        
        Additional Instructions:
        - Don't use vague recommendations like "consider" or "research". Instead, provide direct actionable steps.
            Some examples that you shouldnt follow are:
               1) **Implement Consistent Transaction Categorization**: Take 15 minutes to review and correct the categorization of all recent transactions. 
                    Establish a routine to regularly review and categorize new transactions to ensure accuracy and maintain a clear picture of expenses.
               2) **Review and Optimize Shopping Expenses**: Allocate 30 minutes each month to review shopping expenses and identify areas where costs can be reduced. 
                    Set a goal to decrease shopping expenses by 10% within the next three months by exploring alternative options, such as buying in bulk or using coupons.
               3) **Explore Bill Reduction Strategies**: Dedicate 1 hour to researching ways to reduce bills, such as negotiating with service providers or exploring more affordable alternatives.
                    Aim to decrease bill expenses by 5% within the next two months by implementing cost-saving strategies.

        - Use specific numbers and percentages from the data.
        - Each recommendation should be something the user can start doing today.
        - Avoid generic financial advice. Tailor everything to their specific situation. When user read the reccomendations they are to feel like it is personaly made for them and them only.
        - Don't use special characters or markdown formatting like ** for bold or * for italics. I want just plain text.
        """
        
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.3,
            max_tokens=1000
        )
        
        response_text = response.choices[0].message.content
        
        # Parse insights and recommendations
        insights_section = response_text.split('---INSIGHTS---')[-1].split('---RECOMMENDATIONS---')[0].strip()
        recommendations_section = response_text.split('---RECOMMENDATIONS---')[-1].strip()
        
        # Improved processing for recommendations to remove all markdown
        processed_recommendations = []
        for line in recommendations_section.split('\n'):
            if line.strip():
                # Remove number prefixes like "1. " or "2. "
                clean_line = re.sub(r'^\d+\.\s+', '', line.strip())
                # Properly remove all asterisks (markdown bold/italic)
                clean_line = re.sub(r'\*\*|\*', '', clean_line)
                processed_recommendations.append(clean_line)
        
        # Join the processed recommendations
        final_recommendations = '\n\n'.join(processed_recommendations)
        
        return insights_section, final_recommendations
        
    except Exception as e:
        print(f"Error in Groq API processing: {str(e)}")
        return "Unable to generate insights at this time.", "Please try again later."
    
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

# Dashboard View


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
    search_type = request.GET.get('search_type', 'income')
    month = request.GET.get('month')
    year = request.GET.get('year')
    date = request.GET.get('date')
    category = request.GET.get('category')
    min_amount = request.GET.get('min_amount')
    max_amount = request.GET.get('max_amount')
    keyword = request.GET.get('keyword')
    user = request.user

    incomes = Income.objects.filter(user=user)
    
    if month:
        incomes = incomes.filter(date__month=month)
    if year:
        incomes = incomes.filter(date__year=year)
    if date:
        incomes = incomes.filter(date=date)
    if category:
        incomes = incomes.filter(category__icontains=category)
    if min_amount:
        incomes = incomes.filter(amount__gte=min_amount)
    if max_amount:
        incomes = incomes.filter(amount__lte=max_amount)
    if keyword:
        incomes = incomes.filter(description__icontains=keyword)
        incomes = incomes.order_by('-date')
    total_income = incomes.aggregate(total=models.Sum('amount'))['total'] or 0
    total_expenses = Expense.objects.filter(user=user).aggregate(total=models.Sum('amount'))['total'] or 0
    balance = total_income - total_expenses

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
        
    expense_list = []
    if isinstance(expense_data, dict):
        expense_list = [{'grouper': k, 'total': v['total'], 'list': v['list']} for k, v in expense_data.items()]

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

    # Aggregate income and expenses by category
    income_by_category = Income.objects.filter(user=request.user).values('category').annotate(total_amount=Sum('amount'))
    expense_by_category = Expense.objects.filter(user=request.user).values('category').annotate(total_amount=Sum('amount'))

    # Prepare data for the chart
    categories = list(set([item['category'] for item in income_by_category] + [item['category'] for item in expense_by_category]))
    income_data = [next((item['total_amount'] for item in income_by_category if item['category'] == category), 0) for category in categories]
    expense_data = [next((item['total_amount'] for item in expense_by_category if item['category'] == category), 0) for category in categories]

    context = {
        "total_income": total_income,
        "total_expenses": total_expenses,
        "balance": balance,
        "incomes": Income.objects.filter(user=request.user),
        "expenses": expenses_page,
        "available_months": range(1, 13),   
        "available_years": available_years,
        "chart_labels": chart_labels,
        "chart_income": chart_income,
        "chart_expenses": chart_expenses,
        'categories': categories,
        'income_data': income_data,
        'expense_data': expense_data,
        "expense_list": expense_list,
        'incomes': incomes,
        'search_type': search_type,
        'month': month, 
        'year': year,
        'date': date,
        'category': category,
        'min_amount': min_amount,
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
