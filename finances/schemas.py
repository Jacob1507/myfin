from datetime import datetime
from decimal import Decimal
from typing import Optional

from ninja import Schema


class CreateUserBankTransactionDetailSchema(Schema):
    amount: Decimal
    cash_counter_id: int
    created_at: Optional[datetime] = None
    bank_alias_id: Optional[int] = None


class UserBankTransactionDetailSchema(Schema):
    id: int
    amount: Decimal
    created_at: Optional[datetime] = None
    bank_alias_id: Optional[int] = None


class TimeFramesSchema(Schema):
    from_date: Optional[datetime] = None
    to_date: Optional[datetime] = None


class CreateUserBankAliasSchema(Schema):
    name: str


class UserBankAliasSchema(Schema):
    id: int
    name: str


class CreateUserTransactionCategorySchema(Schema):
    name: str


class UserTransactionCategorySchema(Schema):
    id: int
    name: str


class CreateUserReceiptSchema(Schema):
    created_at: Optional[datetime] = None
    bank_alias_id: Optional[int] = None


class UserReceiptSchema(Schema):
    id: int
    bank_alias_id: Optional[int] = None
    image: str
    created_at: Optional[datetime] = None
