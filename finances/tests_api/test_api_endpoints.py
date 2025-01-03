from datetime import timedelta
from decimal import Decimal

from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse_lazy
from django.utils import timezone
from django.test.client import encode_multipart

from .utils import ApiTestHelper, AllowedMethods, TEST_BOUNDARY
from ..logic import (
    simple_cash_counter_update,
    add_bank_transaction,
    add_new_transaction_category,
    add_new_cash_counter,
    get_user_cash_counter_detail,
    get_user_banks_qs,
    get_user_receipts_qs,
)


class ApiListsTests(ApiTestHelper):
    def test_bank_aliases_empty(self):
        url = reverse_lazy("api-1:bank_aliases_list")
        response = self.as_user(user=self.user, method=AllowedMethods.GET, route=url)
        data = self.get_json_result(response, has_pagination=True)
        self.assertEqual(data, list())

    def test_bank_aliases_correct(self):
        self.setup_bank_aliases()
        url = reverse_lazy("api-1:bank_aliases_list")
        response = self.as_user(user=self.user, method=AllowedMethods.GET, route=url)
        data = self.get_json_result(response, has_pagination=True)
        self.assertEqual(len(data), 3)

    def test_transactions_list_empty(self):
        url = reverse_lazy("api-1:transactions_list")
        response = self.as_user(user=self.user, method=AllowedMethods.GET, route=url)
        data = self.get_json_result(response, has_pagination=True)
        self.assertEqual(data, list())

    def test_transactions_list_correct(self):
        ucc = add_new_cash_counter(user=self.user, name="CC1")
        # Give user some cash
        simple_cash_counter_update(
            user=self.user, cash_counter_id=ucc.id, transaction_amount=Decimal("20.00")
        )
        # Add transaction
        add_bank_transaction(
            user=self.user, transaction_amount=Decimal("-10.0"), cash_counter_id=ucc.id
        )

        url = reverse_lazy("api-1:transactions_list")
        response = self.as_user(user=self.user, method=AllowedMethods.GET, route=url)
        data = self.get_json_result(response, has_pagination=True)
        self.assertEqual(len(data), 1)
        self.assertEqual(
            get_user_cash_counter_detail(user=self.user, cash_counter_id=ucc.id).amount,
            Decimal("10.0"),
        )

    def test_transactions_in_time_frames(self):
        ucc = add_new_cash_counter(user=self.user, name="CC1")
        # Specify time frames
        from_date = self.date_to_string(timezone.now() - timedelta(days=2))
        to_date = self.date_to_string(timezone.now() - timedelta(hours=10))

        far_in_past = timezone.now() - timedelta(days=7)
        in_time_frames = timezone.now() - timedelta(days=1)
        # Add transaction
        transaction1 = add_bank_transaction(
            user=self.user,
            transaction_amount=Decimal("-5.0"),
            created_at=far_in_past,
            cash_counter_id=ucc.id,
        )
        transaction2 = add_bank_transaction(
            user=self.user,
            cash_counter_id=ucc.id,
            transaction_amount=Decimal("-5.0"),
            created_at=in_time_frames,
        )
        transaction3 = add_bank_transaction(
            user=self.user,
            transaction_amount=Decimal("-5.0"),
            created_at=in_time_frames,
            cash_counter_id=ucc.id,
        )

        url = (
            reverse_lazy("api-1:transactions_list")
            + f"?from_date={from_date}&to_date={to_date}"
        )
        response = self.as_user(user=self.user, method=AllowedMethods.GET, route=url)
        data = self.get_json_result(response, has_pagination=True)
        self.assertEqual(len(data), 2, data)
        self.assertEqual(
            data[0]["created_at"], self.dt_to_string(transaction3.created_at)
        )
        self.assertEqual(data[0]["id"], transaction3.id)
        self.assertEqual(
            data[1]["created_at"], self.dt_to_string(transaction2.created_at)
        )
        self.assertEqual(data[1]["id"], transaction2.id)

    def test_receipts_list_empty(self):
        url = reverse_lazy("api-1:receipts_list")
        response = self.as_user(user=self.user, method=AllowedMethods.GET, route=url)
        data = self.get_json_result(response, has_pagination=True)
        self.assertEqual(data, list())

    def test_receipts_list_correct(self):
        self.setup_receipts()
        url = reverse_lazy("api-1:receipts_list")
        response = self.as_user(user=self.user, method=AllowedMethods.GET, route=url)
        data = self.get_json_result(response, has_pagination=True)
        self.assertEqual(len(data), 1)
        self.assertTrue(str(self.user.id) in data[0]["image"])

    def test_transaction_categories_list_empty(self):
        url = reverse_lazy("api-1:transaction_categories_list")
        response = self.as_user(user=self.user, method=AllowedMethods.GET, route=url)
        data = self.get_json_result(response, has_pagination=True)
        self.assertEqual(data, list())

    def test_transaction_categories_list_correct(self):
        category = add_new_transaction_category(user=self.user, name="Restaurants")
        url = reverse_lazy("api-1:transaction_categories_list")
        response = self.as_user(user=self.user, method=AllowedMethods.GET, route=url)
        data = self.get_json_result(response, has_pagination=True)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["id"], category.id)


class ApiCreationTests(ApiTestHelper):
    def test_user_transaction_created_without_dt_and_bank_alias(self):
        ucc = add_new_cash_counter(user=self.user, name="CC1")
        data = dict(amount=Decimal("10.0"), cash_counter_id=ucc.id)
        url = reverse_lazy("api-1:transaction_create")
        response = self.as_user(
            user=self.user, method=AllowedMethods.POST, route=url, data=data
        )
        response_data = self.get_json_result(response)
        self.assertTrue(response_data.get("success", False))

    def test_user_transaction_created_without_dt(self):
        ucc = add_new_cash_counter(user=self.user, name="CC1")
        # Setup bank aliases
        self.setup_bank_aliases()
        # Get some bank alias
        bid = get_user_banks_qs(self.user).first()["id"]
        data = dict(amount=Decimal("-10.0"), bank_alias_id=bid, cash_counter_id=ucc.id)
        url = reverse_lazy("api-1:transaction_create")
        response = self.as_user(
            user=self.user, method=AllowedMethods.POST, route=url, data=data
        )
        response_data = self.get_json_result(response)
        self.assertTrue(response_data.get("success", False))

    def test_user_transaction_created_with_all_data(self):
        ucc = add_new_cash_counter(user=self.user, name="CC1")
        # Setup bank aliases
        self.setup_bank_aliases()
        # Get some bank alias
        bid = get_user_banks_qs(self.user).first()["id"]
        data = dict(
            amount=Decimal("-10.0"),
            bank_alias_id=bid,
            created_at=timezone.now() - timedelta(hours=2),
            cash_counter_id=ucc.id,
        )
        url = reverse_lazy("api-1:transaction_create")
        response = self.as_user(
            user=self.user, method=AllowedMethods.POST, route=url, data=data
        )
        response_data = self.get_json_result(response)
        self.assertTrue(response_data.get("success", False))

    def test_bulk_user_transactions_created_without_dt_and_bank_alias(self):
        ucc = add_new_cash_counter(user=self.user, name="CC1")
        data = [
            dict(amount=Decimal("10.0"), cash_counter_id=ucc.id),
            dict(amount=Decimal("-10.0"), cash_counter_id=ucc.id),
            dict(amount=Decimal("20.00"), cash_counter_id=ucc.id),
        ]
        url = reverse_lazy("api-1:transaction_bulk_create")
        response = self.as_user(
            user=self.user, method=AllowedMethods.POST, route=url, data=data
        )
        response_data = self.get_json_result(response)
        self.assertTrue(response_data.get("success", False))

    def test_bulk_user_transactions_created_without_dt(self):
        ucc = add_new_cash_counter(user=self.user, name="CC1")
        # Setup bank aliases
        self.setup_bank_aliases()
        # Get some bank alias
        bid = get_user_banks_qs(self.user).first()["id"]
        data = [
            dict(amount=Decimal("10.0"), bank_alias_id=bid, cash_counter_id=ucc.id),
            dict(amount=Decimal("-10.0"), bank_alias_id=bid, cash_counter_id=ucc.id),
            dict(amount=Decimal("20.00"), bank_alias_id=bid, cash_counter_id=ucc.id),
        ]
        url = reverse_lazy("api-1:transaction_bulk_create")
        response = self.as_user(
            user=self.user, method=AllowedMethods.POST, route=url, data=data
        )
        response_data = self.get_json_result(response)
        self.assertTrue(response_data.get("success", False))

    def test_bulk_user_transactions_created_with_all_data(self):
        ucc = add_new_cash_counter(user=self.user, name="CC1")
        # Setup bank aliases
        self.setup_bank_aliases()
        # Get some bank alias
        bid = get_user_banks_qs(self.user).first()["id"]
        dt = timezone.now()

        data = [
            dict(
                amount=Decimal("10.0"),
                bank_alias_id=bid,
                created_at=dt - timedelta(hours=1),
                cash_counter_id=ucc.id,
            ),
            dict(
                amount=Decimal("-10.0"),
                bank_alias_id=bid,
                created_at=dt - timedelta(hours=-2),
                cash_counter_id=ucc.id,
            ),
            dict(
                amount=Decimal("20.00"),
                bank_alias_id=bid,
                created_at=dt - timedelta(hours=10),
                cash_counter_id=ucc.id,
            ),
        ]
        url = reverse_lazy("api-1:transaction_bulk_create")
        response = self.as_user(
            user=self.user, method=AllowedMethods.POST, route=url, data=data
        )
        response_data = self.get_json_result(response)
        self.assertTrue(response_data.get("success", False))

    def test_user_creates_new_bank_alias(self):
        data = dict(name="New Bank Alias")
        url = reverse_lazy("api-1:bank_alias_create")
        response = self.as_user(
            user=self.user, method=AllowedMethods.POST, route=url, data=data
        )
        response_data = self.get_json_result(response)
        self.assertTrue(response_data.get("success", False))

    def test_user_creates_new_transactions_category(self):
        data = dict(name="Shopping")
        url = reverse_lazy("api-1:transaction_category_create")
        response = self.as_user(
            user=self.user, method=AllowedMethods.POST, route=url, data=data
        )
        response_data = self.get_json_result(response)
        self.assertTrue(response_data.get("success", False))

    def test_user_adds_new_receipt(self):
        # Setup bank aliases
        self.setup_bank_aliases()
        # Get some bank alias
        bid = get_user_banks_qs(self.user).first()["id"]

        receipts_before = get_user_receipts_qs(user=self.user)
        self.assertEqual(len(receipts_before), 0)

        with open("./finances/tests_api/files/receipt1.png", "rb") as f:
            file = SimpleUploadedFile(
                "test_api_receipt.png", f.read(), content_type="image/png"
            )

        data = dict(
            created_at=timezone.now() - timedelta(hours=1), bank_alias_id=bid, file=file
        )
        content = encode_multipart(TEST_BOUNDARY, data)

        url = reverse_lazy("api-1:receipt_create")
        response = self.as_user(
            user=self.user,
            method=AllowedMethods.POST,
            route=url,
            content_type=f"multipart/form-data; boundary={TEST_BOUNDARY}",
            data=content,
            format="multipart",
        )
        response_data = self.get_json_result(response)
        self.assertTrue(response_data.get("success", False))

        receipts_before = get_user_receipts_qs(user=self.user)
        self.assertEqual(len(receipts_before), 1)
