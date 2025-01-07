from django.core.management.base import BaseCommand

from finances.logic import setup_default_categories


class Command(BaseCommand):
    help = "Create default categories list on database initialization"

    def handle(self, *args, **options):
        setup_default_categories()
