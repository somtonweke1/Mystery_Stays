from django.core.management.base import BaseCommand
from listings.utils.supabase_import import import_properties_from_csv, import_bookings_from_csv
import os
import sys

class Command(BaseCommand):
    help = 'Upload a CSV file to Supabase'

    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str, help='Path to the CSV file')
        parser.add_argument('--type', type=str, choices=['properties', 'bookings'], 
                          help='Type of data in the CSV file (properties or bookings)')

    def handle(self, *args, **options):
        file_path = options['file_path']
        data_type = options['type']

        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR(f'File not found: {file_path}'))
            return

        if not data_type:
            # Try to determine the type from the file name
            if 'properties' in file_path.lower():
                data_type = 'properties'
            elif 'bookings' in file_path.lower():
                data_type = 'bookings'
            else:
                self.stdout.write(self.style.ERROR(
                    'Could not determine data type. Please specify --type properties or --type bookings'
                ))
                return

        try:
            if data_type == 'properties':
                success, message = import_properties_from_csv(file_path)
            else:
                success, message = import_bookings_from_csv(file_path)

            if success:
                self.stdout.write(self.style.SUCCESS(message))
            else:
                self.stdout.write(self.style.ERROR(message))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error processing file: {str(e)}')) 