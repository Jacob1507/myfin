from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import models

from .utils import get_upload_path


User = get_user_model()


class CustomTransactionCategory(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)


class BankAlias(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)


class Receipt(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    bank_alias = models.ForeignKey(
        BankAlias, related_name="receipts", on_delete=models.CASCADE, null=True
    )
    image = models.ImageField(upload_to=get_upload_path)
    created_at = models.DateTimeField()


class BankTransaction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    cash_counter = models.ForeignKey(
        "UserCashCounter", on_delete=models.CASCADE, related_name="bank_transactions"
    )
    bank_alias = models.ForeignKey(
        BankAlias, on_delete=models.PROTECT, related_name="bank_transactions", null=True
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField()
    applied = models.BooleanField(default=False)


class UserCashCounter(models.Model):
    parent = models.ForeignKey(
        "self", on_delete=models.CASCADE, null=True, related_name="children"
    )
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="user_cash_counters"
    )
    name = models.CharField(max_length=50)
    slug = models.SlugField()
    bank_alias = models.ForeignKey(BankAlias, on_delete=models.PROTECT, null=True)
    amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.00")
    )
    updated_at = models.DateTimeField(auto_now_add=True)
