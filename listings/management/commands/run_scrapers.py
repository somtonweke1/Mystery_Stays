# listings/management/commands/run_scrapers.py
from django.core.management.base import BaseCommand
from listings.scraper import run_scrapers
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Run all property scrapers'

    def handle(self, *args, **options):
        try:
            total_properties = run_scrapers()
            self.stdout.write(
                self.style.SUCCESS(f'Successfully scraped {total_properties} properties')
            )
        except Exception as e:
            logger.error(f"Error running scrapers: {str(e)}")
            self.stdout.write(
                self.style.ERROR(f'Error running scrapers: {str(e)}')
            )