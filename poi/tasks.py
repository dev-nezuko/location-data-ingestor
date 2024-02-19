from celery import shared_task
import json
import pandas as pd
import xml.etree.ElementTree as ET
from django.core.exceptions import ValidationError

from .models import PointOfInterest

@shared_task
def process_csv_chunk(file_path):
    """
    Processes and imports data from a CSV file chunk into the PointOfInterest model.

    Args:
        file_path (str): The path to the CSV file to process.
    """
    column_types = {
        'poi_id': str,
        'poi_name': str,
        'poi_category': str,
        'poi_latitude': str,
        'poi_longitude': str,
        'poi_ratings': str,
    }
    chunk_size = 1000

    for chunk in pd.read_csv(file_path, dtype=column_types, chunksize=chunk_size):
        for index, row in chunk.iterrows():
            try:
                internal_id = int(row['poi_id'])
                name = row['poi_name']
                category = row['poi_category']
                latitude = float(row['poi_latitude'])
                longitude = float(row['poi_longitude'])

                ratings_str = row['poi_ratings']
                if not ratings_str.startswith('{') or not ratings_str.endswith('}'):
                    raise ValueError(f'Invalid ratings format: {ratings_str}')

                ratings = [float(rating.strip('{}')) for rating in ratings_str.split(',')]
                average_rating = sum(ratings) / len(ratings)

                PointOfInterest.objects.create(
                    internal_id=internal_id,
                    name=name,
                    category=category,
                    latitude=latitude,
                    longitude=longitude,
                    ratings=average_rating
                )
            except ValueError as e:
                print(f"Skipping row {index} due to ValueError: {e}")
                continue
            except ValidationError as e:
                print(f"Skipping row {index} due to ValidationError: {e}")
                continue
            except Exception as e:
                print(f"Skipping row {index} due to unexpected error: {e}")
                continue

@shared_task
def process_json_file(file_path):
    """
    Processes and imports data from a JSON file into the PointOfInterest model.

    Args:
        file_path (str): The path to the JSON file to process.
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        for item in data:
            ratings = sum(item['ratings']) / len(item['ratings']) if item['ratings'] else 0
            PointOfInterest.objects.create(
                internal_id=item['id'],
                name=item['name'],
                latitude=item['coordinates']['latitude'],
                longitude=item['coordinates']['longitude'],
                category=item['category'],
                ratings=ratings
            )

@shared_task
def process_xml_file(file_path):
    """
    Processes and imports data from an XML file into the PointOfInterest model.

    Args:
        file_path (str): The path to the XML file to process.
    """
    tree = ET.parse(file_path)
    root = tree.getroot()
    for poi_element in root:
        ratings_str = poi_element.find('pratings').text
        ratings = [float(rating) for rating in ratings_str.split(',')]
        average_rating = sum(ratings) / len(ratings) if ratings else 0
        PointOfInterest.objects.create(
            internal_id=poi_element.find('pid').text,
            name=poi_element.find('pname').text,
            latitude=float(poi_element.find('platitude').text),
            longitude=float(poi_element.find('plongitude').text),
            category=poi_element.find('pcategory').text,
            ratings=average_rating
        )
