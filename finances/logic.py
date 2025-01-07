from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional

from django.contrib.auth import get_user_model
from django.core.files import File
from django.conf import settings
from django.db import transaction
from django.db.models import F, Q, QuerySet, Sum, Max, Prefetch
from django.utils import timezone
from django.utils.text import slugify

from accounts.logic import create_user
from .models import (
    BankAlias,
    Transaction,
    Budget,
    TransactionCategory,
    Receipt,
)


User = get_user_model()


IMAGES_DIR = settings.BASE_DIR / "static/images/"

CATEGORIES = {
    "Car": IMAGES_DIR / "car.png",
    "Groceries": IMAGES_DIR / "shopping-cart.png",
    "Credit": IMAGES_DIR / "dollar.png",
    "Restaurants": IMAGES_DIR / "cutlery.png",
    "Savings": IMAGES_DIR / "piggy-bank.png",
    "Investments": IMAGES_DIR / "earning.png",
    "Shopping": IMAGES_DIR / "online-shopping.png",
    "Hobbies": IMAGES_DIR / "mental-health.png",
    "Travelling": IMAGES_DIR / "travel-luggage.png",
}


# INSERTS AND UPDATES


def setup_default_categories(user: User):
    for key, img_path in CATEGORIES.items():
        with open(img_path, "rb") as img:
            file = File(img, name=key + ".png")
            TransactionCategory.objects.get_or_create(user=user, name=key, image=file)


@transaction.atomic
def setup_new_user(*, username: str, password: str, email: str) -> User:
    """Setup required models after user registers"""
    user = create_user(username, password, email)
    root_title = f"{username}-root-counter"
    Budget.objects.get_or_create(
        user=user, parent=None, title=root_title, slug=slugify(root_title)
    )
    setup_default_categories(user)
    return user


@transaction.atomic
def add_new_budget(
    *,
    user: User,
    title: str,
    bank_alias_ids: list[int],
    categories_ids: Optional[list[int]] = None,
    is_shared: bool = False,
) -> Budget:
    if not bank_alias_ids:
        raise ValueError("New budget require at least one bank alias")

    if categories_ids is None:
        categories_ids = list()

    root_budget = get_user_root_budget(user=user)
    new_budget = Budget.objects.create(
        user=user,
        parent=root_budget,
        title=title,
        slug=slugify(title),
        is_shared=is_shared,
    )
    alias_qs = BankAlias.objects.filter(id__in=bank_alias_ids)
    new_budget.bank_aliases.add(*alias_qs)

    categories_qs = TransactionCategory.objects.filter(id__in=categories_ids)
    if categories_qs:
        new_budget.categories.add(*categories_qs)

    return new_budget


def add_new_bank_alias(*, user: User, name: str) -> BankAlias:
    bank_alias, _ = BankAlias.objects.get_or_create(user=user, name=name)
    return bank_alias


def add_new_transaction_category(*, user: User, name: str):
    category, _ = TransactionCategory.objects.get_or_create(user=user, name=name)
    return category


@transaction.atomic
def add_bank_transaction(
    *,
    user: User,
    transaction_amount: Decimal,
    bank_alias: BankAlias,
    budget: Optional[Budget] = None,
    category: Optional[TransactionCategory] = None,
    created_at: Optional[datetime] = None,
    file: Optional[File] = None,
    is_income: bool = False,
) -> Optional[Transaction]:
    if created_at is None:
        created_at = timezone.now()

    updated_budget = simple_budget_update(
        user=user, budget=budget, transaction_amount=transaction_amount
    )
    if not updated_budget:
        return

    new_bank_transaction = Transaction.objects.create(
        user=user,
        bank_alias=bank_alias,
        amount=transaction_amount,
        created_at=created_at,
        applied=True,
    )
    if file:
        add_receipt(
            user=user,
            bank_alias=bank_alias,
            bank_transaction=new_bank_transaction,
            image=file,
        )

    return new_bank_transaction


def add_bulk_transactions(
    *,
    bank_transactions: list,
    user: User,
    bank_alias: BankAlias,
) -> None:
    selected_budget_ids = list(item.bank_alias_id for item in bank_transactions)
    to_objs = list()

    for item in bank_transactions:
        if item.created_at is None:
            item.created_at = timezone.now()

        new_transaction = Transaction(
            user=user,
            bank_alias=bank_alias,
            created_at=item.created_at,
            amount=item.amount,
        )
        to_objs.append(new_transaction)

    with transaction.atomic():
        Transaction.objects.bulk_create(to_objs)
        for budget_id in selected_budget_ids:
            bulk_budget_update(user=user, budget_id=budget_id)

    return None


def add_receipt(
    *,
    image: File,
    user: User,
    bank_alias: BankAlias,
    bank_transaction: Transaction,
    created_at: Optional[datetime] = None,
) -> Receipt:
    """Add user receipt"""
    new_receipt = Receipt(
        user=user, image=image, bank_alias=bank_alias, bank_transaction=bank_transaction
    )
    if created_at is not None:
        new_receipt.created_at = created_at
    else:
        new_receipt.created_at = timezone.now()

    new_receipt.save()
    return new_receipt


@transaction.atomic
def simple_budget_update(
    *, user: User, budget: Budget, transaction_amount: Decimal
) -> Optional[Budget]:
    budget_qs = Budget.objects.filter(user=user).filter(id=budget.id)
    if not budget_qs:
        return

    assert user == budget_qs.first().user
    updated = budget_qs.update(amount=F("amount") + transaction_amount)
    if not updated:
        return

    get_user_root_budget_qs(user=user).update(amount=F("amount") + transaction_amount)
    return budget_qs.first()


@transaction.atomic
def bulk_budget_update(
    *,
    user: User,
    budget_id: int,
) -> None:
    budget_qs = Budget.objects.prefetch_related(
        Prefetch("bank_aliases__bank_transactions", to_attr="bank_transactions")
    ).filter(user=user, id=budget_id)
    if not budget_qs:
        return

    assert user == budget_qs.first().user
    total_value = 0
    for budget in budget_qs:
        transactions = budget.bank_transactions.filter(applied=False).aggregate(
            sum_amount=Sum("amount", default=Decimal("0.00")),
        )
        budget_qs.filter(id=budget.id).update(
            amount=F("amount") + transactions["sum_amount"]
        )
        budget.bank_transactions.filter(applied=False).update(applied=True)
        total_value += transactions["sum_amount"]

    get_user_root_budget_qs(user=user).update(amount=F("amount") + total_value)
    return None


# QUERIES


def get_budgets_summary(*, user: User) -> dict[str, list]:
    budgets_qs = Budget.objects.filter(user=user).exclude(parent__isnull=True)
    summary_qs = budgets_qs.aggregate(
        amount_personal=Sum(
            "amount", default=Decimal("0.00"), filter=Q(is_shared=False)
        ),
        amount_shared=Sum("amount", default=Decimal("0.00"), filter=Q(is_shared=True)),
        last_update_personal=Max("updated_at", filter=Q(is_shared=False)),
        last_update_shared=Max("updated_at", filter=Q(is_shared=True)),
    )
    personal_qs = budgets_qs.filter(is_shared=False).values(
        "id",
        "title",
        "amount",
        "updated_at",
    )
    shared_qs = budgets_qs.filter(is_shared=True).values(
        "id",
        "title",
        "amount",
        "updated_at",
    )
    return dict(
        summary=[
            dict(
                id=None,
                title="Personal budgets",
                amount=summary_qs["amount_personal"],
                updated_at=summary_qs["last_update_personal"],
            ),
            dict(
                id=None,
                title="Shared budgets",
                amount=summary_qs["amount_shared"],
                updated_at=summary_qs["last_update_shared"],
            ),
        ],
        personal=list(personal_qs),
        shared=list(shared_qs),
    )


def get_user_root_budget(*, user: User) -> Budget:
    try:
        return Budget.objects.get(user=user, parent__isnull=True)
    except Budget.DoesNotExist:
        root_title = f"{user.username}-root-counter"
        budget, created = Budget.objects.get_or_create(
            user=user, parent=None, title=root_title, slug=slugify(root_title)
        )
        return budget


def get_budget_detail(*, user: User, budget_id: int) -> Budget:
    return Budget.objects.get(user=user, id=budget_id)


def get_user_root_budget_qs(*, user: User) -> QuerySet[Budget]:
    return Budget.objects.filter(user=user, parent=None)


def get_user_banks_qs(user: User) -> QuerySet[BankAlias]:
    qs = BankAlias.objects.filter(user=user).order_by("name")
    return qs


def get_user_transactions_qs(
    *,
    user: User,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
) -> QuerySet[Transaction]:
    if from_date and to_date:
        assert from_date > to_date, "'from_date' cannot be higher than 'to_date'"
    # date_frames_qs = _get_date_frames_qs(from_date=from_date, to_date=to_date)
    return (
        Transaction.objects.filter(user=user)
        # .filter(date_frames_qs)
        .order_by("-created_at", "-id")
    )


def get_user_receipts_qs(
    *,
    user: User,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
) -> QuerySet[Receipt]:
    # date_frames_qs = _get_date_frames_qs(from_date=from_date, to_date=to_date)
    return (
        Receipt.objects.filter(user=user)
        .values("id", "bank_alias_id", "image", "created_at")
        .order_by("-created_at", "id")
    )


def get_user_transaction_categories_qs(user: User) -> QuerySet[TransactionCategory]:
    return TransactionCategory.objects.filter(user=user)


# def _get_date_frames_qs(
#     *, from_date: Optional[datetime] = None, to_date: Optional[datetime] = None
# ) -> Q:
#     if from_date is None:
#         return Q(created_at__lte=to_date)
#     if to_date is None:
#         to_date = timezone.now()
#     return Q(Q(created_at__lte=to_date), Q(created_at__gte=from_date))
