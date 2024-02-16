'''
File contains logic to handle import poi command
'''
import json
import pandas as pd
import xml.etree.ElementTree as ET
from django.core.management.base import BaseCommand
from poi.models import PointOfInterest

class Command(BaseCommand):
    """
    This command imports Point of Interest (POI) data from CSV, JSON, and XML files.
    """

    help = 'Import PoI data from CSV, JSON, and XML files'

    def add_arguments(self, parser):
        """
        Adds arguments to the command.
        """
        parser.add_argument('files', nargs='+', type=str, help='List of file paths')

    def handle(self, *args, **options):
        """
        Handles the command execution.
        """
        for file_path in options['files']:
            if file_path.endswith('.csv'):
                self.import_csv(file_path)
            elif file_path.endswith('.json'):
                self.import_json(file_path)
            elif file_path.endswith('.xml'):
                self.import_xml(file_path)

        self.stdout.write(self.style.SUCCESS('All files imported successfully'))

    def import_csv(self, file_path):
        """
        Imports POI data from a CSV file.
        """
        try:
            # Define data types for each column
            column_types = {
                'poi_id': str,
                'poi_name': str,
                'poi_category': str,
                'poi_latitude': str,
                'poi_longitude': str,
                'poi_ratings': str
            }

            # Define chunk size
            chunk_size = 1000

            # Read CSV file into chunks
            for chunk in pd.read_csv(file_path, dtype=column_types, chunksize=chunk_size):
                self.process_csv_chunk(chunk)

        except Exception as e:
            self.stderr.write(self.style.ERROR(f'Error importing CSV file: {e}'))

    def process_csv_chunk(self, chunk):
        """
        Processes a chunk of CSV data.
        """
        try:
            # Iterate over rows in the chunk
            for index, row in chunk.iterrows():
                try:
                    # Convert poi_id to integer (if possible)
                    internal_id = int(row['poi_id'])

                    # Extract other data from the row
                    name = row['poi_name']
                    category = row['poi_category']
                    
                    # Convert latitude and longitude to float (if possible)
                    latitude = float(row['poi_latitude'])
                    longitude = float(row['poi_longitude'])

                    ratings_str = row['poi_ratings']
                    if not ratings_str.startswith('{') or not ratings_str.endswith('}'):
                        raise ValueError(f'Invalid ratings format: {ratings_str}')
                    ratings = [float(rating.strip('{}')) for rating in ratings_str.split(',')]
                    average_rating = sum(ratings) / len(ratings)

                    # Create PointOfInterest object
                    poi = PointOfInterest.objects.create(
                        internal_id=internal_id,
                        name=name,
                        category=category,
                        latitude=latitude,
                        longitude=longitude,
                        ratings=average_rating
                    )
                except Exception as e:
                    self.stderr.write(self.style.WARNING(f'Skipping row due to validation error: {e}'))
                    continue

        except Exception as e:
            self.stderr.write(self.style.ERROR(f'Error processing CSV chunk: {e}'))

    def import_json(self, file_path):
        """
        Imports POI data from a JSON file.
        """
        try:
            # Define chunk size
            chunk_size = 1000

            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

                # Split data into chunks
                chunks = [data[i:i+chunk_size] for i in range(0, len(data), chunk_size)]

                # Process each chunk
                for chunk in chunks:
                    self.process_json_chunk(chunk)

        except Exception as e:
            self.stderr.write(self.style.ERROR(f'Error importing JSON file: {e}'))

    def process_json_chunk(self, chunk):
        """
        Processes a chunk of JSON data.
        """
        try:
            for item in chunk:
                poi = PointOfInterest.objects.create(
                    internal_id=item['id'],
                    name=item['name'],
                    latitude=item['coordinates']['latitude'],
                    longitude=item['coordinates']['longitude'],
                    category=item['category'],
                    ratings=sum(item['ratings']) / len(item['ratings']) if item['ratings'] else 0
                )
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'Error processing JSON chunk: {e}'))

    def import_xml(self, file_path):
        """
        Imports POI data from an XML file.
        """
        try:
            # Define chunk size
            chunk_size = 1000

            tree = ET.parse(file_path)
            root = tree.getroot()

            # Split XML data into chunks
            chunks = [root[i:i+chunk_size] for i in range(0, len(root), chunk_size)]

            # Process each chunk
            for chunk in chunks:
                self.process_xml_chunk(chunk)

        except Exception as e:
            self.stderr.write(self.style.ERROR(f'Error importing XML file: {e}'))

    def process_xml_chunk(self, chunk):
        """
        Processes a chunk of XML data.
        """
        try:
            for poi_element in chunk:
                # Parse ratings as a list of floats
                ratings_str = poi_element.find('pratings').text
                ratings = [float(rating) for rating in ratings_str.split(',')]

                # Calculate average rating
                average_rating = sum(ratings) / len(ratings) if ratings else 0

                # Create PointOfInterest object
                poi = PointOfInterest.objects.create(
                    internal_id=poi_element.find('pid').text,
                    name=poi_element.find('pname').text,
                    latitude=float(poi_element.find('platitude').text),
                    longitude=float(poi_element.find('plongitude').text),
                    category=poi_element.find('pcategory').text,
                    ratings=average_rating
                )
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'Error processing XML chunk: {e}'))
