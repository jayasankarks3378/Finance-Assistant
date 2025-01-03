# Register your models here.

from django.contrib import admin
from .models import Income, Expense

admin.site.register(Income)
admin.site.register(Expense)
