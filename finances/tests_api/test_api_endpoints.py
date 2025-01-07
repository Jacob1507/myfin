from datetime import timedelta
from decimal import Decimal
from unittest import skip, expectedFailure

from django.test import TestCase
from django.utils import timezone

from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APIRequestFactory

from finances import views as fin_views
from finances.logic import (
    add_bank_transaction,
    add_new_budget,
    add_new_bank_alias,
    get_user_transactions_qs,
    simple_budget_update,
)
from finances.tests_api.utils import ApiFactoryMixin, setup_test_user


class TransactionsTest(TestCase, ApiFactoryMixin):
    @classmethod
    def setUpTestData(cls):
        cls.factory = APIRequestFactory()

        # Has no pre-created records, only these created during account creation
        cls.clean_user = setup_test_user(username="TMP USER")

        # Has pre-created records: bank alias, budget, some cash
        cls.persisted_user = setup_test_user(username="PERSISTED USER")
        cls.bank_alias = add_new_bank_alias(
            user=cls.persisted_user, name="TEST BANK ALIAS"
        )
        cls.default_budget = add_new_budget(
            user=cls.persisted_user,
            title="TEST BUDGET",
            bank_alias_ids=[cls.bank_alias.id],
        )
        simple_budget_update(
            user=cls.persisted_user,
            transaction_amount=Decimal("20.00"),
            budget=cls.default_budget,
        )

    def test_transactions_list_empty(self):
        url = reverse("transactions-list")
        request = self.factory.get(url, format="json")
        view = fin_views.TransactionsListView.as_view()
        response, data = self.as_user(self.clean_user, request, view)
        self.assertEqual(data, list(), get_user_transactions_qs(user=self.clean_user))

    def test_transactions_added_then_fetched(self):
        url_post = reverse("transaction-create")
        data = dict(
            amount=Decimal("10.00"),  # User can only type in positive numbers
            budget_id=self.default_budget.id,
            bank_alias_id=self.bank_alias.id,
            is_income=False,
            file=None,
        )
        request = self.factory.post(url_post, data, format="json")
        view = fin_views.TransactionCreateView.as_view()
        self.as_user(
            self.persisted_user,
            request,
            view,
            expected_status_code=status.HTTP_201_CREATED,
        )

        url_get = reverse("transactions-list")
        request = self.factory.get(url_get)
        view = fin_views.TransactionsListView.as_view()
        response, data = self.as_user(self.persisted_user, request, view)

        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["amount"], "-10.00")

    @skip("TODO: time frames feature")
    def test_transactions_in_time_frames(self):
        from_date = self.date_to_string(timezone.now() - timedelta(days=2))
        to_date = self.date_to_string(timezone.now() - timedelta(hours=10))

        far_in_past = timezone.now() - timedelta(days=7)
        in_time_frames = timezone.now() - timedelta(days=1)

        transaction1 = add_bank_transaction(
            user=self.persisted_user,
            transaction_amount=Decimal("-5.0"),
            created_at=far_in_past,
            bank_alias=self.bank_alias,
            budget=self.default_budget,
        )
        transaction2 = add_bank_transaction(
            user=self.persisted_user,
            transaction_amount=Decimal("-5.0"),
            created_at=in_time_frames,
            bank_alias=self.bank_alias,
            budget=self.default_budget,
        )
        transaction3 = add_bank_transaction(
            user=self.persisted_user,
            transaction_amount=Decimal("-5.0"),
            created_at=in_time_frames,
            bank_alias=self.bank_alias,
            budget=self.default_budget,
        )

        url = reverse("transactions-list") + f"?from_date={from_date}&to_date={to_date}"
        request = self.factory.get(url)
        view = fin_views.TransactionsListView.as_view()
        response, data = self.as_user(self.persisted_user, request, view)
        self.assertEqual(len(data), 2, data)
        self.assertEqual(
            data[0]["created_at"], self.dt_to_string(transaction3.created_at)
        )
        self.assertEqual(data[0]["id"], transaction3.id)
        self.assertEqual(
            data[1]["created_at"], self.dt_to_string(transaction2.created_at)
        )
        self.assertEqual(data[1]["id"], transaction2.id)

    def test_delete_transaction_then_fetch(self):
        transaction1 = add_bank_transaction(
            user=self.persisted_user,
            transaction_amount=Decimal("-5.0"),
            created_at=timezone.now(),
            bank_alias=self.bank_alias,
            budget=self.default_budget,
        )
        url_get = reverse("transactions-list")
        url_post = reverse("transaction-delete")

        request = self.factory.get(url_get)
        view = fin_views.TransactionsListView.as_view()
        response, data = self.as_user(self.persisted_user, request, view)
        self.assertEqual(len(data), 1)

        request = self.factory.post(url_post, {"id": transaction1.id}, format="json")
        view = fin_views.TransactionDeleteView.as_view()
        self.as_user(self.persisted_user, request, view)

        request = self.factory.get(url_get)
        view = fin_views.TransactionsListView.as_view()
        response, data = self.as_user(self.persisted_user, request, view)
        self.assertEqual(len(data), 0)


class BudgetsTest(TestCase, ApiFactoryMixin):
    @classmethod
    def setUpTestData(cls):
        cls.factory = APIRequestFactory()

        # Has no pre-created records, only these created during account creation
        cls.clean_user = setup_test_user(username="TMP USER")

        # Has pre-created records: bank alias, budget, some cash
        cls.persisted_user = setup_test_user(username="PERSISTED USER")
        cls.bank_alias = add_new_bank_alias(
            user=cls.persisted_user, name="TEST BANK ALIAS"
        )
        cls.default_budget = add_new_budget(
            user=cls.persisted_user,
            title="TEST BUDGET",
            bank_alias_ids=[cls.bank_alias.id],
        )
        simple_budget_update(
            user=cls.persisted_user,
            transaction_amount=Decimal("20.00"),
            budget=cls.default_budget,
        )

    def test_initial_budget_setup(self):
        url = reverse("budgets-summary-list")

        request = self.factory.get(url)
        view = fin_views.BudgetsSummaryView.as_view()
        response, data = self.as_user(self.clean_user, request, view)

        self.assertNotEqual(data["summary"], [])
        for item in data["summary"]:
            self.assertIsNone(item["id"])
            self.assertIsNone(item["updated_at"])
            self.assertEqual(item["amount"], "0.00")

        self.assertEqual(data["personal"], [])
        self.assertEqual(data["shared"], [])

    def test_add_not_shared_budget_then_fetch(self):
        url_get = reverse("budgets-summary-list")
        url_post = reverse("budget-create")
        bank_alias = add_new_bank_alias(user=self.clean_user, name="tmp bank alias")

        new_budget_data = dict(
            title="tmp budget",
            bank_alias_ids=[bank_alias.id],
            categories_ids=[],
            is_shared=False,
        )
        request = self.factory.post(url_post, new_budget_data, format="json")
        view = fin_views.BudgetCreateView.as_view()
        self.as_user(
            self.clean_user, request, view, expected_status_code=status.HTTP_201_CREATED
        )

        request = self.factory.get(url_get)
        view = fin_views.BudgetsSummaryView.as_view()
        response, data = self.as_user(self.clean_user, request, view)

        self.assertEqual(data["shared"], [])

        for item in data["personal"]:
            if item["title"] == new_budget_data["title"]:
                self.assertIsNotNone(item["id"])
                self.assertIsNotNone(item["updated_at"])
                self.assertEqual(item["amount"], "0.00")
            else:
                self.fail(f"Assertions not raised. Expected data {new_budget_data}")

    def test_delete_budget_then_fetch(self):
        url_get = reverse("budgets-summary-list")
        url_post = reverse("budget-delete")

        request = self.factory.post(
            url_post, {"id": self.default_budget.id}, format="json"
        )
        view = fin_views.BudgetDeleteView.as_view()
        self.as_user(self.persisted_user, request, view)

        request = self.factory.get(url_get)
        view = fin_views.BudgetsSummaryView.as_view()
        response, data = self.as_user(self.persisted_user, request, view)
        self.assertEqual(data["personal"], [])
        self.assertEqual(data["shared"], [])

    @expectedFailure
    def test_only_desired_budget_will_recieve_updates(self):
        self.fail("Not implemented")

    @expectedFailure
    def test_add_multiple_banks_to_budget(self):
        self.fail("Not implemented")


class BankAliasesTest(TestCase, ApiFactoryMixin):
    @classmethod
    def setUpTestData(cls):
        cls.factory = APIRequestFactory()

        # Has no pre-created records, only these created during account creation
        cls.clean_user = setup_test_user(username="TMP USER")

        # Has pre-created records: bank alias, budget, some cash
        cls.persisted_user = setup_test_user(username="PERSISTED USER")
        cls.bank_alias = add_new_bank_alias(
            user=cls.persisted_user, name="TEST BANK ALIAS"
        )
        cls.default_budget = add_new_budget(
            user=cls.persisted_user,
            title="TEST BUDGET",
            bank_alias_ids=[cls.bank_alias.id],
        )
        simple_budget_update(
            user=cls.persisted_user,
            transaction_amount=Decimal("20.00"),
            budget=cls.default_budget,
        )

    def test_bank_aliases_empty(self):
        url = reverse("bank-aliases-list")
        request = self.factory.get(url, format="json")
        view = fin_views.BankAliasesListView.as_view()
        response, data = self.as_user(self.clean_user, request, view)
        self.assertEqual(data, [])

    def test_bank_alias_correctly_added(self):
        url_get = reverse("bank-aliases-list")
        url_post = reverse("bank-alias-create")

        request = self.factory.post(url_post, {"name": "tmp bank"}, format="json")
        view = fin_views.BankAliasCreateView.as_view()
        self.as_user(
            self.clean_user, request, view, expected_status_code=status.HTTP_201_CREATED
        )

        request = self.factory.get(url_get)
        view = fin_views.BankAliasesListView.as_view()
        response, data = self.as_user(self.clean_user, request, view)
        self.assertEqual(len(data), 1)

    def test_delete_bank_alias(self):
        url_get = reverse("bank-aliases-list")
        url_post = reverse("bank-alias-create")
        bank_alias = add_new_bank_alias(user=self.clean_user, name="tmp bank")

        request = self.factory.get(url_get)
        view = fin_views.BankAliasesListView.as_view()
        response, data = self.as_user(self.clean_user, request, view)
        self.assertEqual(len(data), 1)

        request = self.factory.post(url_post, {"id": bank_alias.id}, format="json")
        view = fin_views.BankAliasDeleteView.as_view()
        self.as_user(self.clean_user, request, view)


class CategoriesTest(TestCase, ApiFactoryMixin):
    @classmethod
    def setUpTestData(cls):
        cls.factory = APIRequestFactory()

        # Has no pre-created records, only these created during account creation
        cls.clean_user = setup_test_user(username="TMP USER")

        # Has pre-created records: bank alias, budget, some cash
        cls.persisted_user = setup_test_user(username="PERSISTED USER")
        cls.bank_alias = add_new_bank_alias(
            user=cls.persisted_user, name="TEST BANK ALIAS"
        )
        cls.default_budget = add_new_budget(
            user=cls.persisted_user,
            title="TEST BUDGET",
            bank_alias_ids=[cls.bank_alias.id],
        )
        simple_budget_update(
            user=cls.persisted_user,
            transaction_amount=Decimal("20.00"),
            budget=cls.default_budget,
        )

    def test_transaction_categories_init_setup(self):
        url = reverse("transaction-categories-list")
        request = self.factory.get(url)
        view = fin_views.TransactionCategoriesListView.as_view()
        response, data = self.as_user(self.clean_user, request, view)
        self.assertEqual(len(data), 9, self.clean_user.username)

    def test_add_transaction_then_fetch(self):
        url_post = reverse("transaction-category-create")
        data = dict(name="tmp category")
        view = fin_views.TransactionCategoryCreateView.as_view()
        request = self.factory.post(url_post, data, format="json")
        self.as_user(self.clean_user, request, view, status.HTTP_201_CREATED)

        url_get = reverse("transaction-categories-list")
        request = self.factory.get(url_get)
        view = fin_views.TransactionCategoriesListView.as_view()
        response, data = self.as_user(self.clean_user, request, view)
        self.assertEqual(len(data), 10)


class ReceiptsTests(TestCase, ApiFactoryMixin):
    @classmethod
    def setUpTestData(cls):
        cls.factory = APIRequestFactory()

        # Has no pre-created records, only these created during account creation
        cls.clean_user = setup_test_user(username="TMP USER")

        # Has pre-created records: bank alias, budget, some cash
        cls.persisted_user = setup_test_user(username="PERSISTED USER")
        cls.bank_alias = add_new_bank_alias(
            user=cls.persisted_user, name="TEST BANK ALIAS"
        )
        cls.default_budget = add_new_budget(
            user=cls.persisted_user,
            title="TEST BUDGET",
            bank_alias_ids=[cls.bank_alias.id],
        )
        simple_budget_update(
            user=cls.persisted_user,
            transaction_amount=Decimal("20.00"),
            budget=cls.default_budget,
        )

    @expectedFailure
    def test_receipts_list_empty(self):
        self.fail("Not implemented")

    @expectedFailure
    def test_receipts_list_correct(self):
        self.fail("Not implemented")
