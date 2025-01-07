from django.shortcuts import get_object_or_404

from rest_framework import permissions, status
from rest_framework.views import APIView, Response
from rest_framework.generics import ListAPIView

from finances import logic as fin_logic
from finances.models import Budget, BankAlias, Transaction, TransactionCategory
from finances.serializers import (
    BudgetsSummarySerializer,
    BudgetCreateSerializer,
    BudgetDeleteSerializer,
    BankAliasesListSerializer,
    BankAliasCreateSerializer,
    BankAliasDeleteSerializer,
    TransactionItemSerializer,
    TransactionCreateSerializer,
    TransactionDeleteSerializer,
    TransactionCategoriesListSerializer,
    TransactionCategoryCreateSerializer,
    TransactionCategoryDeleteSerializer,
)


class BudgetsSummaryView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, *args, **kwargs):
        data = fin_logic.get_budgets_summary(user=self.request.user)
        serializer = BudgetsSummarySerializer(data=data)
        serializer.is_valid(raise_exception=True)
        return Response(status=status.HTTP_200_OK, data=serializer.data)


class BudgetCreateView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        serializer = BudgetCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        fin_logic.add_new_budget(
            user=self.request.user,
            title=serializer.validated_data.get("title"),
            bank_alias_ids=serializer.validated_data.get("bank_alias_ids"),
            categories_ids=serializer.validated_data.get("categories_ids"),
            is_shared=serializer.validated_data.get("is_shared", False),
        )
        return Response(
            status=status.HTTP_201_CREATED, data=dict(message="Budget created")
        )


class BudgetDeleteView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, *args, **kwargs):
        serializer = BudgetDeleteSerializer(data=self.request.data)
        serializer.is_valid(raise_exception=True)
        obj = get_object_or_404(Budget, id=serializer.validated_data.get("id"))
        obj.delete()
        return Response(status=status.HTTP_200_OK, data=dict(message="Budget deleted"))


class BankAliasesListView(ListAPIView):
    serializer_class = BankAliasesListSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return fin_logic.get_user_banks_qs(self.request.user)


class BankAliasCreateView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        serializer = BankAliasCreateSerializer(data=self.request.data)
        serializer.is_valid(raise_exception=True)
        fin_logic.add_new_bank_alias(
            user=self.request.user, name=serializer.validated_data.get("name")
        )
        return Response(
            status=status.HTTP_201_CREATED, data=dict(message="Bank alias created")
        )


class BankAliasDeleteView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, *args, **kwargs):
        serializer = BankAliasDeleteSerializer(data=self.request.data)
        serializer.is_valid(raise_exception=True)
        obj = get_object_or_404(BankAlias, id=serializer.validated_data.get("id"))
        obj.delete()
        return Response(
            status=status.HTTP_200_OK, data=dict(message="Bank alias deleted")
        )


class TransactionsListView(ListAPIView):
    serializer_class = TransactionItemSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return fin_logic.get_user_transactions_qs(user=self.request.user)


class TransactionCreateView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, *args, **kwargs):
        serializer = TransactionCreateSerializer(data=self.request.data)
        serializer.is_valid(raise_exception=True)
        budget = get_object_or_404(
            Budget, id=serializer.validated_data.get("budget_id")
        )
        bank_alias = get_object_or_404(
            BankAlias, id=serializer.validated_data.get("bank_alias_id")
        )
        transaction_amount = serializer.validated_data.get("amount")
        is_income = serializer.validated_data.get("is_income", False)
        if not is_income:
            transaction_amount *= -1
        fin_logic.add_bank_transaction(
            user=self.request.user,
            bank_alias=bank_alias,
            budget=budget,
            transaction_amount=transaction_amount,
            created_at=serializer.validated_data.get("created_at"),
            file=serializer.validated_data.get("file"),
        )
        return Response(
            status=status.HTTP_201_CREATED, data=dict(message="Transaction added")
        )


class TransactionDeleteView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, *args, **kwargs):
        serializer = TransactionDeleteSerializer(data=self.request.data)
        serializer.is_valid(raise_exception=True)
        obj = get_object_or_404(Transaction, id=serializer.validated_data.get("id"))
        obj.delete()
        return Response(
            status=status.HTTP_200_OK, data=dict(message="Transaction deleted")
        )


class TransactionCategoriesListView(ListAPIView):
    serializer_class = TransactionCategoriesListSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return fin_logic.get_user_transaction_categories_qs(self.request.user)


class TransactionCategoryCreateView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, *args, **kwargs):
        serializer = TransactionCategoryCreateSerializer(data=self.request.data)
        serializer.is_valid(raise_exception=True)
        fin_logic.add_new_transaction_category(
            user=self.request.user, name=serializer.validated_data.get("name")
        )
        return Response(
            status=status.HTTP_201_CREATED,
            data=dict(message="Transaction category created"),
        )


class TransactionCategoryDeleteView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, *args, **kwargs):
        serializer = TransactionCategoryDeleteSerializer(data=self.request.data)
        serializer.is_valid(raise_exception=True)
        obj = get_object_or_404(
            TransactionCategory, id=serializer.validated_data.get("id")
        )
        obj.delete()
        return Response(
            status=status.HTTP_200_OK, data=dict(message="Transaction category deleted")
        )
