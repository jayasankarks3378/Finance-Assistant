# finances/models.py
from django.db import models

class Income(models.Model):
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.CharField(max_length=255)
    date = models.DateField()
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE)

    def __str__(self):
        return f"Income of {self.amount} on {self.date} by {self.user}"

    class Meta:
        verbose_name = "Income"
        verbose_name_plural = "Incomes"
        ordering = ['-date']
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['date']),
        ]

class Expense(models.Model):
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.CharField(max_length=255)
    date = models.DateField()
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE)

    def __str__(self):
        return f"Expense of {self.amount} on {self.date} in {self.category.name} by {self.user}"

    class Meta:
        verbose_name = "Expense"
        verbose_name_plural = "Expenses"
        ordering = ['-date']
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['date']),
        ]

