from rest_framework import serializers


class BudgetSummaryItemSerializer(serializers.Serializer):
    id = serializers.IntegerField(allow_null=True, required=False)
    title = serializers.CharField(required=False)
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    updated_at = serializers.DateTimeField(allow_null=True, required=False)


class BudgetsSummarySerializer(serializers.Serializer):
    summary = serializers.ListSerializer(child=BudgetSummaryItemSerializer())
    personal = serializers.ListSerializer(child=BudgetSummaryItemSerializer())
    shared = serializers.ListSerializer(child=BudgetSummaryItemSerializer())


class BudgetCreateSerializer(serializers.Serializer):
    title = serializers.CharField()
    bank_alias_ids = serializers.ListField()
    categories_ids = serializers.ListField()
    is_shared = serializers.BooleanField()


class BudgetDeleteSerializer(serializers.Serializer):
    id = serializers.IntegerField()


class BankAliasesListSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()


class BankAliasCreateSerializer(serializers.Serializer):
    name = serializers.CharField()


class BankAliasDeleteSerializer(serializers.Serializer):
    id = serializers.IntegerField()


class TransactionItemSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    created_at = serializers.DateTimeField(default=None)
    bank_alias_id = serializers.IntegerField(default=None)


class TransactionCreateSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    created_at = serializers.DateTimeField(default=None)
    budget_id = serializers.IntegerField()
    category_id = serializers.IntegerField(default=None)
    bank_alias_id = serializers.IntegerField()
    is_income = serializers.BooleanField(default=False)
    file = serializers.ImageField(default=None, allow_null=True)


class TransactionDeleteSerializer(serializers.Serializer):
    id = serializers.IntegerField()


class TransactionCategoryCreateSerializer(serializers.Serializer):
    name = serializers.CharField()


class TransactionCategoryDeleteSerializer(serializers.Serializer):
    id = serializers.IntegerField()


class TransactionCategoriesListSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    image = serializers.CharField()
