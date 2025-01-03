from datetime import datetime
from typing import Optional

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile

from ninja.testing import TestClient
from ninja.responses import Response
from ninja_jwt.tokens import RefreshToken

from ..logic import (
    add_new_bank_alias,
    add_new_transaction_category,
    add_receipt,
    setup_new_user,
)
from ..api import router


User = get_user_model()


class AllowedMethods:
    POST = "post"
    GET = "get"
    as_list = [POST, GET]


TEST_BOUNDARY = "BoUnDaRyStRiNg"
TEST_BANK_ALIASES = ["BANK1", "BANK2", "BANK3"]
TEST_TRANSACTION_CATEGORIES = ["shopping", "car", "restaurants"]
DEFAULT_PASSWORD = "1234"


class ApiTestHelper(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Client setup
        cls.client = TestClient(router)
        # Default records
        cls.user = setup_new_user(
            username="Test user 1", password=DEFAULT_PASSWORD, email="test@xyz.com"
        )
        cls.user2 = setup_new_user(
            username="Test user 2", password=DEFAULT_PASSWORD, email="test2@xyz.com"
        )
        cls.user3 = setup_new_user(
            username="Test user 3", password=DEFAULT_PASSWORD, email="test3@xyz.com"
        )

    def setup_bank_aliases(self):
        for user in [self.user, self.user2, self.user3]:
            for alias in TEST_BANK_ALIASES:
                add_new_bank_alias(user=user, name=alias)

    def setup_transaction_categories(self):
        for user in [self.user, self.user2, self.user3]:
            for category_name in TEST_TRANSACTION_CATEGORIES:
                add_new_transaction_category(user=user, name=category_name)

    def setup_receipts(self, bank_alias_id: Optional[int] = None):
        for user in [self.user, self.user2, self.user3]:
            with open("./finances/tests_api/files/receipt1.png", "rb") as f:
                data = f.read()
                add_receipt(
                    image=ContentFile(data, name="user_upload.png"),
                    user=user,
                    bank_alias_id=bank_alias_id,
                )

    def as_user(
        self,
        *,
        user: User,
        method: str,
        route: str,
        content_type: str = "application/json",
        **kwargs
    ) -> Response:
        """Helper method to allow API access for test users"""
        assert method in AllowedMethods.as_list
        # Assure that user always has valid access token
        refresh = RefreshToken.for_user(user)
        new = dict(refresh=str(refresh), access=str(refresh.access_token))
        headers = {
            "Authorization": "Bearer " + new["access"],
        }
        response: Response = getattr(self.client, method)(
            route, headers=headers, content_type=content_type, **kwargs
        )
        return response

    def get_json_result(
        self,
        response: Response,
        has_pagination: bool = False,
        expected_status_code: int = 200,
    ):
        """Returns API JSON response"""
        self.assertEqual(response.status_code, expected_status_code, response.json())
        if has_pagination:
            return response.json().get("items")
        else:
            return response.json()

    @staticmethod
    def date_to_string(dt: datetime):
        return dt.strftime("%Y-%m-%d")

    @staticmethod
    def dt_to_string(dt: datetime):
        return dt.isoformat(timespec="milliseconds").replace("+00:00", "Z")
