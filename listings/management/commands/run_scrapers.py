# listings/management/commands/run_scrapers.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from listings.scrapers import run_all_scrapers, mark_outdated_listings

class Command(BaseCommand):
    help = 'Run property scrapers for the specified locations'

    def add_arguments(self, parser):
        parser.add_argument('--locations', nargs='+', type=str, help='Locations to scrape')
        parser.add_argument('--max-pages', type=int, default=3, help='Maximum number of pages to scrape per location')
        parser.add_argument('--mark-outdated', action='store_true', help='Mark outdated listings before scraping')

    def handle(self, *args, **options):
        locations = options['locations']
        max_pages = options['max_pages']
        
        self.stdout.write(f"Starting scrapers for locations: {', '.join(locations)}")
        self.stdout.write(f"Max pages per location: {max_pages}")
        
        if options['mark_outdated']:
            self.stdout.write("Marking outdated listings...")
            mark_outdated_listings()
        
        start_time = timezone.now()
        run_all_scrapers(locations, max_pages)
        end_time = timezone.now()
        
        self.stdout.write(self.style.SUCCESS(f"Scraping completed in {(end_time - start_time).total_seconds()} seconds"))