from datetime import datetime
from decimal import Decimal
from typing import Optional

from django.contrib.auth import get_user_model
from django.core.files import File
from django.db import transaction
from django.db.models import F, Q, QuerySet, Sum
from django.utils import timezone
from django.utils.text import slugify

from accounts.logic import create_user
from .models import (
    BankAlias,
    BankTransaction,
    UserCashCounter,
    CustomTransactionCategory,
    Receipt,
)
from .schemas import CreateUserBankTransactionDetailSchema


User = get_user_model()


# INSERTS AND UPDATES


@transaction.atomic
def setup_new_user(*, username: str, password: str, email: str) -> User:
    """Setup required models after user registers"""
    user = create_user(username, password, email)
    root_name = f"{username}-root-counter"
    UserCashCounter.objects.get_or_create(
        user=user, parent=None, name=root_name, slug=slugify(root_name)
    )
    return user


def add_new_cash_counter(
    *, user: User, name: str, bank_alias: Optional[BankAlias] = None
) -> UserCashCounter:
    root_ucc = get_user_root_counter(user=user)
    return UserCashCounter.objects.create(
        user=user,
        bank_alias=bank_alias,
        parent=root_ucc,
        name=name,
        slug=slugify(name),
    )


def add_new_bank_alias(*, user: User, name: str) -> BankAlias:
    """Create new bank alias for user"""
    bank_alias, _ = BankAlias.objects.get_or_create(user=user, name=name)
    return bank_alias


def add_new_transaction_category(*, user: User, name: str):
    return CustomTransactionCategory.objects.create(user=user, name=name)


def add_bank_transaction(
    *,
    user: User,
    cash_counter_id: int,
    transaction_amount: Decimal,
    bank_alias_id: Optional[int] = None,
    created_at: Optional[datetime] = None,
) -> Optional[BankTransaction]:
    """Add new bank transaction"""
    bank_alias = _get_bank_alias_qs(bank_alias_id)

    if created_at is None:
        created_at = timezone.now()

    with transaction.atomic():
        ucc = simple_cash_counter_update(
            user=user,
            cash_counter_id=cash_counter_id,
            transaction_amount=transaction_amount,
        )
        if not ucc:
            return

        new_transaction = BankTransaction.objects.create(
            user=user,
            cash_counter=ucc,
            bank_alias=bank_alias,
            amount=transaction_amount,
            created_at=created_at,
            applied=True,
        )

    return new_transaction


def add_bulk_transactions(
    *,
    bank_transactions: list[CreateUserBankTransactionDetailSchema],
    user: User,
    bank_alias_id: Optional[int] = None,
) -> None:
    """Bulk creation for bank transactions"""
    bank_alias = _get_bank_alias_qs(bank_alias_id)
    selected_ucc_ids = set(item.cash_counter_id for item in bank_transactions)
    selected_ucc_qs = UserCashCounter.objects.filter(user=user).filter(
        id__in=selected_ucc_ids
    )

    to_objs = list()

    for item in bank_transactions:
        if item.created_at is None:
            item.created_at = timezone.now()

        new_transaction = BankTransaction(
            user=user,
            bank_alias=bank_alias,
            created_at=item.created_at,
            amount=item.amount,
            cash_counter=selected_ucc_qs.get(id=item.cash_counter_id),
        )
        to_objs.append(new_transaction)

    with transaction.atomic():
        BankTransaction.objects.bulk_create(to_objs)
        for ucc_id in selected_ucc_ids:
            bulk_cash_counter_update(user=user, cash_counter_id=ucc_id)

    return None


def add_receipt(
    *,
    image: File,
    user: User,
    created_at: Optional[datetime] = None,
    bank_alias_id: Optional[int] = None,
) -> Receipt:
    """Add user receipt"""
    bank_alias = _get_bank_alias_qs(bank_alias_id)
    new_receipt = Receipt(user=user, image=image, bank_alias=bank_alias)
    if created_at is not None:
        new_receipt.created_at = created_at
    else:
        new_receipt.created_at = timezone.now()

    new_receipt.save()
    return new_receipt


@transaction.atomic
def simple_cash_counter_update(
    *, user: User, cash_counter_id: int, transaction_amount: Decimal
) -> Optional[UserCashCounter]:
    ucc_qs = UserCashCounter.objects.filter(user=user).filter(id=cash_counter_id)
    if not ucc_qs:
        return

    assert user == ucc_qs.first().user
    updated = ucc_qs.update(amount=F("amount") + transaction_amount)
    if not updated:
        return

    get_user_root_counter_qs(user=user).update(amount=F("amount") + transaction_amount)
    return ucc_qs.first()


@transaction.atomic
def bulk_cash_counter_update(
    *,
    user: User,
    cash_counter_id: int,
) -> None:
    ucc_qs = UserCashCounter.objects.prefetch_related("bank_transactions").filter(
        user=user, id=cash_counter_id
    )
    if not ucc_qs:
        return

    assert user == ucc_qs.first().user
    total_value = 0
    for ucc in ucc_qs:
        transactions = ucc.bank_transactions.filter(applied=False).aggregate(
            sum_amount=Sum("amount", default=Decimal("0.00")),
        )
        ucc_qs.filter(id=ucc.id).update(amount=F("amount") + transactions["sum_amount"])
        ucc.bank_transactions.filter(applied=False).update(applied=True)
        total_value += transactions["sum_amount"]

    get_user_root_counter_qs(user=user).update(amount=F("amount") + total_value)
    return None


# QUERIES


def get_user_root_counter(*, user: User) -> UserCashCounter:
    return UserCashCounter.objects.get(user=user, parent=None)


def get_user_root_counter_qs(*, user: User) -> QuerySet[UserCashCounter]:
    return UserCashCounter.objects.filter(user=user, parent=None)


def _get_bank_alias_qs(bank_alias_id: Optional[int]) -> Optional[BankAlias]:
    """Helper function to retrieve bank alias by id, if exists"""
    bank_alias = None
    if bank_alias_id is not None:
        bank_alias = BankAlias.objects.get(id=bank_alias_id)
    return bank_alias


def get_user_cash_counters(
    *, user: User, bank_alias: Optional[BankAlias] = None
) -> QuerySet[UserCashCounter]:
    return UserCashCounter.objects.filter(user=user, bank_alias=bank_alias)


def get_user_cash_counter_detail(
    *, user: User, cash_counter_id: int
) -> UserCashCounter:
    return UserCashCounter.objects.get(user=user, id=cash_counter_id)


def get_user_banks_qs(user: User) -> QuerySet[BankAlias]:
    return BankAlias.objects.filter(user=user).values("id", "name").order_by("name")


def get_user_transactions_qs(
    *,
    user: User,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
) -> QuerySet[BankTransaction]:
    if from_date and to_date:
        assert from_date <= to_date, "'from_date' cannot be higher than 'to_date'"

    date_frames_qs = _get_date_frames_qs(from_date=from_date, to_date=to_date)
    return (
        BankTransaction.objects.filter(user=user)
        .filter(date_frames_qs)
        .values("id", "amount", "created_at", "bank_alias_id", "applied")
        .order_by("-created_at", "-id")
    )


def get_user_receipts_qs(
    *,
    user: User,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
) -> QuerySet[Receipt]:
    date_frames_qs = _get_date_frames_qs(from_date=from_date, to_date=to_date)
    return (
        Receipt.objects.filter(user=user)
        .filter(date_frames_qs)
        .values("id", "bank_alias_id", "image", "created_at")
        .order_by("-created_at", "id")
    )


def get_user_transaction_categories_qs(user: User) -> CustomTransactionCategory:
    return CustomTransactionCategory.objects.filter(user=user)


def _get_date_frames_qs(
    *, from_date: Optional[datetime] = None, to_date: Optional[datetime] = None
) -> Q:
    if from_date is None:
        from_date = timezone.now().replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        )
    if to_date is None:
        to_date = timezone.now()
    return Q(Q(created_at__lte=to_date), Q(created_at__gte=from_date))
