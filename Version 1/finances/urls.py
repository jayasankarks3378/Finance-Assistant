# finances/urls.py
from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

app_name = 'finances'

urlpatterns = [
    path('signup/', views.signup, name='signup'),
    path('login/', auth_views.LoginView.as_view(template_name='finances/login.html'), name='login'),  # Use custom template path
    path('home/', views.home, name='home'),
    #path('logout/', views.logout_view, name='logout'),
    path('logout/', auth_views.LogoutView.as_view(next_page='finances:login'), name='logout'),  # Redirect to login page
    path('dashboard/', views.dashboard, name='dashboard'),

    

    # Income URLs
    path('add_income/', views.add_income, name='add_income'),
    path('edit_income/<int:income_id>/', views.edit_income, name='edit_income'),
    path('delete_income/<int:income_id>/', views.delete_income, name='delete_income'),

    # Expense URLs
    path('add_expense/', views.add_expense, name='add_expense'),
    path('edit_expense/<int:expense_id>/', views.edit_expense, name='edit_expense'),
    path('delete_expense/<int:expense_id>/', views.delete_expense, name='delete_expense'),

]

