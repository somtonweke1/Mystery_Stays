import logging
from django.core.management.base import BaseCommand
from listings.scrapers import run_all_scrapers, mark_outdated_listings

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Run property listing scrapers to fetch voucher-friendly properties'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--locations',
            nargs='+',
            type=str,
            help='List of locations to search (cities or ZIP codes)'
        )
        
        parser.add_argument(
            '--max-pages',
            type=int,
            default=2,
            help='Maximum number of pages to scrape per location and source'
        )
        
        parser.add_argument(
            '--mark-outdated',
            action='store_true',
            help='Mark properties as unavailable if they have not been updated recently'
        )
        
        parser.add_argument(
            '--outdated-days',
            type=int,
            default=30,
            help='Number of days after which a property is considered outdated'
        )
    
    def handle(self, *args, **options):
        locations = options.get('locations')
        max_pages = options.get('max_pages')
        
        if not locations:
            self.stdout.write('No locations specified, using defaults')
        
        # Run the scrapers
        self.stdout.write(f'Running scrapers for {len(locations) if locations else "default"} locations...')
        results = run_all_scrapers(locations=locations, max_pages=max_pages)
        
        # Report results
        self.stdout.write(self.style.SUCCESS(f'Scraping completed. Found {results["total"]} voucher-friendly properties:'))
        self.stdout.write(f'  - Zillow: {results["zillow"]}')
        self.stdout.write(f'  - Apartments.com: {results["apartments"]}')
        
        # Mark outdated listings if requested
        if options.get('mark_outdated'):
            days = options.get('outdated_days')
            count = mark_outdated_listings(days=days)
            self.stdout.write(self.style.SUCCESS(f'Marked {count} properties as unavailable (not updated in {days} days)'))