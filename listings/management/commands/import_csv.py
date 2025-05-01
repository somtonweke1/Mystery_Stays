from django.core.management.base import BaseCommand
from listings.utils.csv_importer import import_properties_from_csv
import os

class Command(BaseCommand):
    help = 'Import properties from CSV file into database'

    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str, help='Path to the CSV file')

    def handle(self, *args, **options):
        file_path = options['file_path']

        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR(f'File not found: {file_path}'))
            return

        try:
            success, message = import_properties_from_csv(file_path)
            if success:
                self.stdout.write(self.style.SUCCESS(message))
            else:
                self.stdout.write(self.style.ERROR(message))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error importing file: {str(e)}')) 