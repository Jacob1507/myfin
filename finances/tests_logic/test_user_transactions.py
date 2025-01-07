from decimal import Decimal
from unittest import skip

from django.test import TestCase
from django.db.utils import IntegrityError

from finances import logic as fin_logic


class UserTransactionsLogicTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = fin_logic.setup_new_user(
            username="main", password="1234", email="test@xyz.pl"
        )
        cls.bank_alias = fin_logic.add_new_bank_alias(
            user=cls.user, name="Test bank alias"
        )
        cls.bank_alias2 = fin_logic.add_new_bank_alias(
            user=cls.user, name="Test bank alias 2"
        )
        cls.budget = fin_logic.add_new_budget(
            user=cls.user, title="Vault1", bank_alias_ids=[cls.bank_alias.id]
        )
        cls.budget2 = fin_logic.add_new_budget(
            user=cls.user, title="Vault2", bank_alias_ids=[cls.bank_alias2.id]
        )

    @staticmethod
    def setup_fresh_user(username: str = "test"):
        return fin_logic.setup_new_user(
            username=username, password="1234", email="test@xyz.pl"
        )

    def test_user_has_created_root_budget(self):
        root_budget = self.user.budgets.filter(parent=None)
        self.assertEqual(root_budget.count(), 1)
        self.assertEqual(root_budget[0].amount, Decimal("0.00"))

    def test_user_cannot_have_multiple_root_budgets(self):
        with self.assertRaises(IntegrityError):
            self.setup_fresh_user(username="main")

        root_budget = self.user.budgets.filter(parent=None)
        self.assertEqual(root_budget.count(), 1)
        self.assertEqual(root_budget[0].amount, Decimal("0.00"))

    def test_children_budget_has_correctly_assigned_parent(self):
        root_budget = fin_logic.get_user_root_budget(user=self.user)
        self.assertEqual(self.budget.parent, root_budget)

    def test_user_created_new_budget(self):
        budget = fin_logic.add_new_budget(
            user=self.user, title="New Vault", bank_alias_ids=[self.bank_alias2.id]
        )
        self.assertEqual(budget.amount, Decimal("0.00"))

    def test_user_budget_correctly_count_amounts(self):
        root_budget = fin_logic.get_user_root_budget(user=self.user)
        fin_logic.add_bank_transaction(
            user=self.user,
            budget=self.budget,
            bank_alias=self.bank_alias,
            transaction_amount=Decimal("100.0"),
        )
        fin_logic.add_bank_transaction(
            user=self.user,
            budget=self.budget,
            bank_alias=self.bank_alias,
            transaction_amount=Decimal("-99.0"),
        )
        self.budget.refresh_from_db()
        root_budget.refresh_from_db()

        self.assertEqual(self.budget.amount, Decimal("1.0"))
        self.assertEqual(root_budget.amount, Decimal("1.0"))

    def test_multiple_user_budgets_work_correctly_with_root_counter(self):
        root_budget = fin_logic.get_user_root_budget(user=self.user)

        fin_logic.add_bank_transaction(
            user=self.user,
            budget=self.budget,
            bank_alias=self.bank_alias,
            transaction_amount=Decimal("100.0"),
        )
        fin_logic.add_bank_transaction(
            user=self.user,
            budget=self.budget2,
            bank_alias=self.bank_alias,
            transaction_amount=Decimal("200.0"),
        )

        self.budget.refresh_from_db()
        self.budget2.refresh_from_db()
        root_budget.refresh_from_db()

        self.assertEqual(self.budget.amount, Decimal("100.0"))
        self.assertEqual(self.budget2.amount, Decimal("200.0"))
        self.assertEqual(root_budget.amount, Decimal("300.0"))

    @skip("TODO: Bulk updates")
    def test_bulk_transaction_has_correct_amounts_for_single_budget(self):
        root_budget = fin_logic.get_user_root_budget(user=self.user)

        # bank_transactions = [
        #     CreateUserBankTransactionDetailSchema(
        #         amount=Decimal("10.0"), bank_alias_id=self.bank_alias.id
        #     )
        #     for _ in range(10)
        # ]
        # fin_logic.add_bulk_transactions(
        #     bank_transactions=bank_transactions, user=self.user
        # )

        self.budget.refresh_from_db()
        root_budget.refresh_from_db()

        self.assertEqual(self.budget.amount, Decimal("100.0"))
        self.assertEqual(root_budget.amount, Decimal("100.0"))

    @skip("TODO: Bulk updates")
    def test_bulk_transaction_has_correct_amounts_for_mixed_budgets(self):
        root_cc = fin_logic.get_user_root_budget(user=self.user)
        bank_transactions = list()
        # for i in range(10):
        #     bank_transactions.append(
        #         CreateUserBankTransactionDetailSchema(
        #             amount=Decimal("10.0"), bank_alias_id=self.bank_alias.id
        #         )
        #     )
        #     bank_transactions.append(
        #         CreateUserBankTransactionDetailSchema(
        #             amount=Decimal("10.0"), bank_alias_id=self.bank_alias2.id
        #         )
        #     )
        #
        # fin_logic.add_bulk_transactions(
        #     bank_transactions=bank_transactions, user=self.user
        # )

        self.budget.refresh_from_db()
        self.budget2.refresh_from_db()
        root_cc.refresh_from_db()

        self.assertEqual(self.budget.amount, Decimal("100.0"))
        self.assertEqual(self.budget2.amount, Decimal("100.0"))
        self.assertEqual(root_cc.amount, Decimal("200.0"))

    @skip("TODO: Bulk updates")
    def test_bulk_transactions_race_conditions(self):
        root_cc = fin_logic.get_user_root_budget(user=self.user)

        # bank_transactions = [
        #     CreateUserBankTransactionDetailSchema(
        #         amount=Decimal("10.0"), bank_alias_id=self.bank_alias.id
        #     )
        #     for _ in range(10)
        # ]
        #
        # fin_logic.add_bulk_transactions(
        #     bank_transactions=bank_transactions, user=self.user
        # )

        # Should be applied only once no matter the amount of calls
        fin_logic.bulk_budget_update(user=self.user, budget_id=self.budget.id)
        fin_logic.bulk_budget_update(user=self.user, budget_id=self.budget.id)

        self.budget.refresh_from_db()
        root_cc.refresh_from_db()
        self.assertEqual(self.budget.amount, Decimal("100.0"))
        self.assertEqual(root_cc.amount, Decimal("100.0"))

    @skip("TODO: Bulk updates")
    def test_bulk_transactions_mixed_with_single_transactions(self):
        root_budget = fin_logic.get_user_root_budget(user=self.user)
        bank_transactions = list()
        # for i in range(10):
        #     bank_transactions.append(
        #         CreateUserBankTransactionDetailSchema(
        #             amount=Decimal("10.0"), bank_alias_id=self.bank_alias.id
        #         )
        #     )
        #     bank_transactions.append(
        #         CreateUserBankTransactionDetailSchema(
        #             amount=Decimal("10.0"), bank_alias_id=self.bank_alias2.id
        #         )
        #     )
        # fin_logic.add_bulk_transactions(
        #     bank_transactions=bank_transactions, user=self.user
        # )
        fin_logic.add_bank_transaction(
            user=self.user,
            budget=self.budget,
            bank_alias=self.bank_alias,
            transaction_amount=Decimal("50.0"),
        )
        fin_logic.add_bank_transaction(
            user=self.user,
            budget=self.budget2,
            bank_alias=self.bank_alias,
            transaction_amount=Decimal("100.0"),
        )

        root_budget.refresh_from_db()
        self.budget.refresh_from_db()
        self.budget2.refresh_from_db()

        self.assertEqual(root_budget.amount, Decimal("350.0"))
        self.assertEqual(self.budget.amount, Decimal("150.0"))
        self.assertEqual(self.budget2.amount, Decimal("200.0"))
