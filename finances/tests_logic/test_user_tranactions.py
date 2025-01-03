from decimal import Decimal

from django.test import TestCase
from django.db.utils import IntegrityError

from finances import logic as fin_logic
from finances.schemas import CreateUserBankTransactionDetailSchema


class UserTransactionsLogicTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = fin_logic.setup_new_user(
            username="main", password="1234", email="test@xyz.pl"
        )
        cls.new_cc = fin_logic.add_new_cash_counter(user=cls.user, name="Vault1")
        cls.new_cc2 = fin_logic.add_new_cash_counter(user=cls.user, name="Vault2")

    @staticmethod
    def setup_fresh_user(username: str = "test"):
        return fin_logic.setup_new_user(
            username=username, password="1234", email="test@xyz.pl"
        )

    def test_user_has_created_root_cash_counter(self):
        root_cc = self.user.user_cash_counters.filter(parent=None)
        self.assertEqual(root_cc.count(), 1)
        self.assertEqual(root_cc[0].amount, Decimal("0.00"))

    def test_user_cannot_have_root_challenges(self):
        with self.assertRaises(IntegrityError):
            self.setup_fresh_user(username="main")

        root_cc = self.user.user_cash_counters.filter(parent=None)
        self.assertEqual(root_cc.count(), 1)
        self.assertEqual(root_cc[0].amount, Decimal("0.00"))

    def test_children_cash_counter_has_correctly_assigned_parent(self):
        root_cc = fin_logic.get_user_root_counter(user=self.user)
        self.assertEqual(self.new_cc.parent, root_cc)

    def test_user_created_new_cash_counter(self):
        new_cc = fin_logic.add_new_cash_counter(user=self.user, name="Vault1")
        self.assertEqual(new_cc.amount, Decimal("0.00"))

    def test_user_cash_counter_correctly_count_amounts(self):
        root_cc = fin_logic.get_user_root_counter(user=self.user)
        fin_logic.add_bank_transaction(
            user=self.user,
            cash_counter_id=self.new_cc.id,
            transaction_amount=Decimal("100.0"),
        )
        fin_logic.add_bank_transaction(
            user=self.user,
            cash_counter_id=self.new_cc.id,
            transaction_amount=Decimal("-99.0"),
        )
        self.new_cc.refresh_from_db()
        root_cc.refresh_from_db()

        self.assertEqual(self.new_cc.amount, Decimal("1.0"))
        self.assertEqual(root_cc.amount, Decimal("1.0"))

    def test_multiple_user_cash_counters_work_correctly_with_root_counter(self):
        root_cc = fin_logic.get_user_root_counter(user=self.user)

        fin_logic.add_bank_transaction(
            user=self.user,
            cash_counter_id=self.new_cc.id,
            transaction_amount=Decimal("100.0"),
        )
        fin_logic.add_bank_transaction(
            user=self.user,
            cash_counter_id=self.new_cc2.id,
            transaction_amount=Decimal("200.0"),
        )

        self.new_cc.refresh_from_db()
        self.new_cc2.refresh_from_db()
        root_cc.refresh_from_db()

        self.assertEqual(self.new_cc.amount, Decimal("100.0"))
        self.assertEqual(self.new_cc2.amount, Decimal("200.0"))
        self.assertEqual(root_cc.amount, Decimal("300.0"))

    def test_bulk_transaction_has_correct_amounts_for_single_cash_counter(self):
        root_cc = fin_logic.get_user_root_counter(user=self.user)

        bank_transactions = [
            CreateUserBankTransactionDetailSchema(
                amount=Decimal("10.0"), cash_counter_id=self.new_cc.id
            )
            for i in range(10)
        ]
        fin_logic.add_bulk_transactions(
            bank_transactions=bank_transactions, user=self.user
        )

        self.new_cc.refresh_from_db()
        root_cc.refresh_from_db()

        self.assertEqual(self.new_cc.amount, Decimal("100.0"))
        self.assertEqual(root_cc.amount, Decimal("100.0"))

    def test_bulk_transaction_has_correct_amounts_for_mixed_cash_counters(self):
        root_cc = fin_logic.get_user_root_counter(user=self.user)
        bank_transactions = list()
        for i in range(10):
            bank_transactions.append(
                CreateUserBankTransactionDetailSchema(
                    amount=Decimal("10.0"), cash_counter_id=self.new_cc.id
                )
            )
            bank_transactions.append(
                CreateUserBankTransactionDetailSchema(
                    amount=Decimal("10.0"), cash_counter_id=self.new_cc2.id
                )
            )

        fin_logic.add_bulk_transactions(
            bank_transactions=bank_transactions, user=self.user
        )

        self.new_cc.refresh_from_db()
        self.new_cc2.refresh_from_db()
        root_cc.refresh_from_db()

        self.assertEqual(self.new_cc.amount, Decimal("100.0"))
        self.assertEqual(self.new_cc2.amount, Decimal("100.0"))
        self.assertEqual(root_cc.amount, Decimal("200.0"))

    def test_bulk_transactions_race_conditions(self):
        root_cc = fin_logic.get_user_root_counter(user=self.user)

        bank_transactions = [
            CreateUserBankTransactionDetailSchema(
                amount=Decimal("10.0"), cash_counter_id=self.new_cc.id
            )
            for _ in range(10)
        ]

        fin_logic.add_bulk_transactions(
            bank_transactions=bank_transactions, user=self.user
        )

        # Should be applied only once no matter the amount of calls
        fin_logic.bulk_cash_counter_update(
            user=self.user, cash_counter_id=self.new_cc.id
        )
        fin_logic.bulk_cash_counter_update(
            user=self.user, cash_counter_id=self.new_cc.id
        )

        self.new_cc.refresh_from_db()
        root_cc.refresh_from_db()
        self.assertEqual(self.new_cc.amount, Decimal("100.0"))
        self.assertEqual(root_cc.amount, Decimal("100.0"))

    def test_bulk_transactions_mixed_with_single_transactions(self):
        root_cc = fin_logic.get_user_root_counter(user=self.user)
        bank_transactions = list()
        for i in range(10):
            bank_transactions.append(
                CreateUserBankTransactionDetailSchema(
                    amount=Decimal("10.0"), cash_counter_id=self.new_cc.id
                )
            )
            bank_transactions.append(
                CreateUserBankTransactionDetailSchema(
                    amount=Decimal("10.0"), cash_counter_id=self.new_cc2.id
                )
            )
        fin_logic.add_bulk_transactions(
            bank_transactions=bank_transactions, user=self.user
        )
        fin_logic.add_bank_transaction(
            user=self.user,
            cash_counter_id=self.new_cc.id,
            transaction_amount=Decimal("50.0"),
        )
        fin_logic.add_bank_transaction(
            user=self.user,
            cash_counter_id=self.new_cc2.id,
            transaction_amount=Decimal("100.0"),
        )

        root_cc.refresh_from_db()
        self.new_cc.refresh_from_db()
        self.new_cc2.refresh_from_db()

        self.assertEqual(root_cc.amount, Decimal("350.0"))
        self.assertEqual(self.new_cc.amount, Decimal("150.0"))
        self.assertEqual(self.new_cc2.amount, Decimal("200.0"))
