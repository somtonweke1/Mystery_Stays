from django.core.management.base import BaseCommand
from listings.utils.convert_csv import convert_avodah_csv
import os

class Command(BaseCommand):
    help = 'Convert Avodah CSV format to property listing format'

    def add_arguments(self, parser):
        parser.add_argument('input_file', type=str, help='Path to the input CSV file')
        parser.add_argument('--output', type=str, help='Path to save the converted CSV file')

    def handle(self, *args, **options):
        input_file = options['input_file']
        output_file = options.get('output', 'converted_properties.csv')

        if not os.path.exists(input_file):
            self.stdout.write(self.style.ERROR(f'Input file not found: {input_file}'))
            return

        try:
            converted_file = convert_avodah_csv(input_file, output_file)
            self.stdout.write(self.style.SUCCESS(f'Successfully converted CSV file to: {converted_file}'))
            
            # Ask if user wants to upload the converted file
            upload = input('Would you like to upload the converted file to Supabase? (y/n): ')
            if upload.lower() == 'y':
                from django.core.management import call_command
                call_command('upload_csv', converted_file, '--type', 'properties')
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error converting file: {str(e)}')) 