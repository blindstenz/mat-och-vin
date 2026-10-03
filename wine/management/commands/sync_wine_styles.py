from django.core.management.base import BaseCommand

from wine.models import WineStyle
from wine.styles_data import WINE_STYLES, sync_styles


class Command(BaseCommand):
    help = "Create or update the wine style reference table from wine/styles_data.py."

    def handle(self, *args, **options):
        sync_styles(WineStyle)
        self.stdout.write(self.style.SUCCESS(f"{len(WINE_STYLES)} vinstilar uppdaterade."))
