from decimal import Decimal

from django.test import TestCase

from finances import logic as fin_logic


class BudgetsTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = fin_logic.setup_new_user(
            username="Test user", password="1234", email="test@xyz.pl"
        )
        cls.other_user = fin_logic.setup_new_user(
            username="Other user", password="1234", email="test2@xyz.pl"
        )

        cls.shopping_category = fin_logic.add_new_transaction_category(
            user=cls.user, name="Shopping"
        )
        cls.restaurants_category = fin_logic.add_new_transaction_category(
            user=cls.user, name="Restaurants"
        )

    def test_budget_created_without_categories(self):
        bank_alias = fin_logic.add_new_bank_alias(user=self.user, name="Bank 1")
        new_budget = fin_logic.add_new_budget(
            user=self.user, title="Vault1.1", bank_alias_ids=[bank_alias.id]
        )
        self.assertEqual(new_budget.title, "Vault1.1")
        self.assertEqual(new_budget.amount, Decimal("0.00"))
        self.assertEqual(new_budget.bank_aliases.all().first(), bank_alias)

    def test_budget_created_with_categories(self):
        bank_alias = fin_logic.add_new_bank_alias(user=self.user, name="Bank 1")
        new_budget = fin_logic.add_new_budget(
            user=self.user,
            title="Vault1.2",
            bank_alias_ids=[bank_alias.id],
            categories_ids=[self.shopping_category.id, self.restaurants_category.id],
        )
        self.assertEqual(new_budget.title, "Vault1.2")
        self.assertEqual(new_budget.amount, Decimal("0.00"))
        self.assertListEqual(
            list(new_budget.categories.all()),
            [self.restaurants_category, self.shopping_category],
        )

    def test_budget_raises_error_when_bank_aliases_not_provided(self):
        with self.assertRaises(ValueError):
            fin_logic.add_new_budget(
                user=self.user,
                title="Broken Vault",
                bank_alias_ids=[],
                categories_ids=[
                    self.shopping_category.id,
                    self.restaurants_category.id,
                ],
            )
