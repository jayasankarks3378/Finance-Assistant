# Generated by Django 4.2.17 on 2025-01-03 08:58

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('finances', '0002_alter_category_options_alter_expense_options_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='expense',
            options={'ordering': ['-date'], 'verbose_name': 'Expense', 'verbose_name_plural': 'Expenses'},
        ),
        migrations.AlterModelOptions(
            name='income',
            options={'ordering': ['-date'], 'verbose_name': 'Income', 'verbose_name_plural': 'Incomes'},
        ),
    ]