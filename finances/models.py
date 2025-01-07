from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import models

from .utils import get_upload_path


User = get_user_model()


class TransactionCategory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    image = models.ImageField(upload_to=get_upload_path)

    class Meta:
        unique_together = ("user", "name")


class BankAlias(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.00")
    )

    class Meta:
        unique_together = ("user", "name")


class Transaction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    bank_alias = models.ForeignKey(
        BankAlias, on_delete=models.CASCADE, related_name="bank_transactions"
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField()
    applied = models.BooleanField(default=True)


class Receipt(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    bank_alias = models.ForeignKey(
        BankAlias, related_name="receipts", on_delete=models.CASCADE, null=True
    )
    bank_transaction = models.ForeignKey(
        Transaction, related_name="receipts", on_delete=models.CASCADE
    )
    image = models.ImageField(upload_to=get_upload_path)


class Budget(models.Model):
    parent = models.ForeignKey(
        "self", on_delete=models.CASCADE, null=True, related_name="children"
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="budgets")
    title = models.CharField(max_length=50, blank=False, null=False, unique=True)
    slug = models.SlugField()
    bank_aliases = models.ManyToManyField(BankAlias, related_name="budgets")
    categories = models.ManyToManyField(TransactionCategory, related_name="budgets")
    amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.00")
    )
    is_shared = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "slug")
