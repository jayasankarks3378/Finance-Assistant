# finances/models.py
from django.db import models

class Income(models.Model):
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.CharField(max_length=255)
    date = models.DateField()
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    category = models.CharField(max_length=255, null=True, blank=True)

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
    category = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f"Expense of {self.amount} on {self.date} by {self.user}"

    class Meta:
        verbose_name = "Expense"
        verbose_name_plural = "Expenses"
        ordering = ['-date'] 
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['date']),
        ]

class BillUpload(models.Model):
    file = models.ImageField(upload_to='uploads/bills/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    processed = models.BooleanField(default=False)
    
    def __str__(self):
        return f"Bill uploaded by {self.user} at {self.uploaded_at}"