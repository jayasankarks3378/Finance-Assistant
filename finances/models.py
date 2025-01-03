# finances/models.py
from django.db import models
from django.contrib.auth.models import User

# class Category(models.Model):
#     name = models.CharField(max_length=100)

#     def __str__(self):
#         return self.name

#     class Meta:
#         verbose_name = "Category"
#         verbose_name_plural = "Categories"

class Income(models.Model):
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.CharField(max_length=255)
    date = models.DateField()
    #category = models.ForeignKey(Category, null=True, blank=True, on_delete=models.SET_NULL)  # optional category for income
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE)

    def __str__(self):
        return f"Income of {self.amount} on {self.date}"

    class Meta:
        verbose_name = "Income"
        verbose_name_plural = "Incomes"
        ordering = ['-date']
        indexes = [
            models.Index(fields=['user']),
            # models.Index(fields=['category']),
            models.Index(fields=['date']),
        ]

# class Expense(models.Model):
#     amount = models.DecimalField(max_digits=10, decimal_places=2)
#     description = models.CharField(max_length=255)
#     date = models.DateField()
#     category = models.ForeignKey(Category, on_delete=models.CASCADE)
#     user = models.ForeignKey('auth.User', on_delete=models.CASCADE)

#     def __str__(self):
#         return f"Expense of {self.amount} on {self.date} in {self.category.name}"

#     class Meta:
#         verbose_name = "Expense"
#         verbose_name_plural = "Expenses"
#         ordering = ['-date']
#         indexes = [
#             models.Index(fields=['user']),
#             models.Index(fields=['category']),
#             models.Index(fields=['date']),
#         ]


# Category model for categorizing expenses

class Expense(models.Model):
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.CharField(max_length=255)
    date = models.DateField()
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return f"Expense of {self.amount} on {self.date} in {self.category.name}"

    class Meta:
        verbose_name = "Expense"
        verbose_name_plural = "Expenses"
        ordering = ['-date']
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['date']),
        ]
