from django.urls import path

from finances import views as fin_views


urlpatterns = [
    path("user-setup/", fin_views.UserSetupView.as_view(), name="user-setup"),
    path(
        "budgets-summary/",
        fin_views.BudgetsSummaryView.as_view(),
        name="budgets-summary-list",
    ),
    path("budgets/create/", fin_views.BudgetCreateView.as_view(), name="budget-create"),
    path("budgets/delete/", fin_views.BudgetDeleteView.as_view(), name="budget-delete"),
    path(
        "bank-aliases/",
        fin_views.BankAliasesListView.as_view(),
        name="bank-aliases-list",
    ),
    path(
        "bank-aliases/create/",
        fin_views.BankAliasCreateView.as_view(),
        name="bank-alias-create",
    ),
    path(
        "bank-aliases/delete/",
        fin_views.BankAliasDeleteView.as_view(),
        name="bank-alias-delete",
    ),
    path(
        "transactions/",
        fin_views.TransactionsListView.as_view(),
        name="transactions-list",
    ),
    path(
        "transactions/create/",
        fin_views.TransactionCreateView.as_view(),
        name="transaction-create",
    ),
    path(
        "transactions/delete/",
        fin_views.TransactionDeleteView.as_view(),
        name="transaction-delete",
    ),
    # TODO: bulk transaction uploads
    # path(
    #     "transactions/bulk-create/",
    #     fin_views.BudgetsSummaryView.as_view(),
    #     name="transactions-bulk-create",
    # ),
    path(
        "transactions/categories/",
        fin_views.TransactionCategoriesListView.as_view(),
        name="transaction-categories-list",
    ),
    path(
        "transactions/categories/create/",
        fin_views.TransactionCategoryCreateView.as_view(),
        name="transaction-category-create",
    ),
    path(
        "transactions/categories/delete/",
        fin_views.TransactionCategoryDeleteView.as_view(),
        name="transaction-category-delete",
    ),
]
