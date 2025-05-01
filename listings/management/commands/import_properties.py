from django.core.management.base import BaseCommand
from listings.utils.supabase_import import import_properties_from_csv, import_bookings_from_csv
import os

class Command(BaseCommand):
    help = 'Import properties and bookings from CSV files to Supabase'

    def add_arguments(self, parser):
        parser.add_argument('--properties', type=str, help='Path to properties CSV file')
        parser.add_argument('--bookings', type=str, help='Path to bookings CSV file')

    def handle(self, *args, **options):
        properties_file = options.get('properties')
        bookings_file = options.get('bookings')

        if properties_file:
            if not os.path.exists(properties_file):
                self.stdout.write(self.style.ERROR(f'Properties file not found: {properties_file}'))
                return

            success, message = import_properties_from_csv(properties_file)
            if success:
                self.stdout.write(self.style.SUCCESS(message))
            else:
                self.stdout.write(self.style.ERROR(message))

        if bookings_file:
            if not os.path.exists(bookings_file):
                self.stdout.write(self.style.ERROR(f'Bookings file not found: {bookings_file}'))
                return

            success, message = import_bookings_from_csv(bookings_file)
            if success:
                self.stdout.write(self.style.SUCCESS(message))
            else:
                self.stdout.write(self.style.ERROR(message))

        if not properties_file and not bookings_file:
            self.stdout.write(self.style.WARNING('Please specify at least one file to import')) 