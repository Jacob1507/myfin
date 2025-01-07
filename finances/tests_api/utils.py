from datetime import datetime
from typing import Optional

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.test.client import MULTIPART_CONTENT, BOUNDARY, encode_multipart

from rest_framework import status
from rest_framework.test import APITestCase, force_authenticate

from ..logic import setup_new_user


User = get_user_model()


def setup_test_user(
    *, username: str, password: Optional[str] = None, email: Optional[str] = None
) -> User:
    """Setup required models after user registers"""
    if password is None:
        password = "test1234"

    if email is None:
        email = "user@testmail.com"

    user = setup_new_user(username=username, password=password, email=email)
    return user


class ApiFactoryMixin:

    def as_user(self, user, request, view, expected_status_code=None) -> tuple:
        if expected_status_code is None:
            expected_status_code = status.HTTP_200_OK

        force_authenticate(request, user=user)
        response = view(request)
        force_authenticate(request, user=None)

        data = getattr(response, "data")
        self.assertEqual(response.status_code, expected_status_code, data)
        return response, data

    @staticmethod
    def date_to_string(dt: datetime):
        return dt.strftime("%Y-%m-%d")

    @staticmethod
    def dt_to_string(dt: datetime):
        return dt.isoformat(timespec="milliseconds").replace("+00:00", "Z")
