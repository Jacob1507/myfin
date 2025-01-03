from ninja import Router, UploadedFile
from ninja import Form, File, Query
from ninja.pagination import paginate, PageNumberPagination
from ninja_jwt.authentication import JWTAuth

from finances import logic as fin_logic
from .schemas import (
    UserBankAliasSchema,
    UserBankTransactionDetailSchema,
    CreateUserBankTransactionDetailSchema,
    TimeFramesSchema,
    UserTransactionCategorySchema,
    CreateUserTransactionCategorySchema,
    UserReceiptSchema,
    CreateUserReceiptSchema,
    CreateUserBankAliasSchema,
)

router = Router(auth=JWTAuth())


@router.get(
    "/bank-aliases/", response=list[UserBankAliasSchema], url_name="bank_aliases_list"
)
@paginate(PageNumberPagination, page_size=10)
def get_user_bank_aliases(request):
    return fin_logic.get_user_banks_qs(request.auth)


@router.post("/banks-aliases/create/", url_name="bank_alias_create")
def create_user_bank_alias(request, data: CreateUserBankAliasSchema):
    fin_logic.add_new_bank_alias(user=request.auth, name=data.name)
    return 200, dict(success=True)


@router.get(
    "/transactions/",
    response=list[UserBankTransactionDetailSchema],
    url_name="transactions_list",
)
@paginate
def get_user_transactions(request, data: TimeFramesSchema = Query(...)):
    return fin_logic.get_user_transactions_qs(
        user=request.auth, from_date=data.from_date, to_date=data.to_date
    )


@router.post("/transactions/create/", url_name="transaction_create")
def create_user_transaction(request, data: CreateUserBankTransactionDetailSchema):
    new_transaction = fin_logic.add_bank_transaction(
        user=request.auth,
        cash_counter_id=data.cash_counter_id,
        transaction_amount=data.amount,
        bank_alias_id=data.bank_alias_id,
        created_at=data.created_at,
    )
    if new_transaction is None:
        return dict(success=False)
    return dict(success=True)


@router.post("/transactions/bulk-create/", url_name="transaction_bulk_create")
def create_bulk_user_transactions(
    request, data: list[CreateUserBankTransactionDetailSchema]
):
    if not data:
        return 200, dict(success=False, msg="No data provided")

    bid = data[0].bank_alias_id
    fin_logic.add_bulk_transactions(
        bank_transactions=data,
        user=request.auth,
        bank_alias_id=bid,
    )
    return dict(success=True)


@router.get("/receipts/", response=list[UserReceiptSchema], url_name="receipts_list")
@paginate(PageNumberPagination, page_size=20)
def get_user_receipts(request, data: TimeFramesSchema = Query(...)):
    return fin_logic.get_user_receipts_qs(
        user=request.auth, from_date=data.from_date, to_date=data.to_date
    )


@router.post("/receipts/create/", url_name="receipt_create")
def create_user_receipt(
    request, data: Form[CreateUserReceiptSchema], file: File[UploadedFile]
):
    fin_logic.add_receipt(
        image=file,
        user=request.auth,
        created_at=data.created_at,
        bank_alias_id=data.bank_alias_id,
    )
    return dict(success=True)


@router.post("/transactions/categories/create/", url_name="transaction_category_create")
def create_new_transaction_category(request, data: CreateUserTransactionCategorySchema):
    fin_logic.add_new_transaction_category(user=request.auth, name=data.name)
    return dict(success=True)


@router.get(
    "/transactions/categories/",
    response=list[UserTransactionCategorySchema],
    url_name="transaction_categories_list",
)
@paginate
def get_transaction_categories(request):
    return fin_logic.get_user_transaction_categories_qs(request.auth)


# @router.get("/uploaded-files/", response=List[FileSchema])
# def files_list(request):
#     uploads = CsvUpload.objects.filter(user=request.auth).values("id", "file")
#     return list(uploads)
#
#
# @router.post("/upload-csv/")
# def csv_upload(request, file: UploadedFile = File(...)):
#     CsvUpload.objects.create(user=request.auth, file=file)
#     return dict(msg="File uploaded", status=200)
