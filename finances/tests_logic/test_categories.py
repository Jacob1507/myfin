from django.test import TestCase

from finances import logic as fin_logic


class TransactionCategoriesTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = fin_logic.setup_new_user(
            username="test user", password="1234", email=""
        )
        cls.other_user = fin_logic.setup_new_user(
            username="other test user", password="1234", email=""
        )

    def test_transaction_category_created_for_user(self):
        tc = fin_logic.add_new_transaction_category(user=self.user, name="Transport")
        self.assertEqual(tc.name, "Transport")

    def test_transaction_category_names_cannot_be_duplicated_for_single_user(self):
        fin_logic.add_new_transaction_category(user=self.user, name="Duplication")
        fin_logic.add_new_transaction_category(user=self.user, name="Duplication")
        self.assertEqual(
            fin_logic.get_user_transaction_categories_qs(self.user)
            .filter(name="Duplication")
            .count(),
            1,
        )
