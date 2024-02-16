import csv
import json
import logging
import math
import xml.etree.ElementTree as ET

from celery import shared_task
from django.core.exceptions import ValidationError
from django.db import transaction

from .models import PointOfInterest

logger = logging.getLogger(__name__)

CSV_FIELDS = ('poi_id', 'poi_name', 'poi_category', 'poi_latitude', 'poi_longitude', 'poi_ratings')


def create_poi(**values):
    for field in ('latitude', 'longitude', 'ratings'):
        value = float(values[field])
        if not math.isfinite(value):
            raise ValueError('Coordinates and ratings must be finite')
        values[field] = value
    if not -90 <= values['latitude'] <= 90 or not -180 <= values['longitude'] <= 180:
        raise ValueError('Coordinates outside latitude/longitude bounds')
    point = PointOfInterest(**values)
    point.full_clean()
    point.save()
    return point


def average_csv_ratings(value):
    if not value.startswith('{') or not value.endswith('}'):
        raise ValueError('CSV ratings must be brace-delimited, e.g. {5,4,3}')
    ratings = [float(rating) for rating in value[1:-1].split(',')]
    return sum(ratings) / len(ratings)


@shared_task
def process_csv_chunk(file_path):
    """
    Import a CSV file, skipping rows that fail parsing or model validation.

    Blank cells stay empty strings, so model validation rejects them instead of
    a missing name being stored as the text "nan".
    """
    with open(file_path, newline='', encoding='utf-8-sig') as source:
        reader = csv.DictReader(source)
        for row in reader:
            values = {field: (row.get(field) or '').strip() for field in CSV_FIELDS}
            try:
                create_poi(
                    internal_id=values['poi_id'],
                    name=values['poi_name'],
                    category=values['poi_category'],
                    latitude=values['poi_latitude'],
                    longitude=values['poi_longitude'],
                    ratings=average_csv_ratings(values['poi_ratings']),
                )
            except (ValueError, ValidationError):
                logger.warning('Skipping invalid CSV line %d', reader.line_num)


@shared_task
@transaction.atomic
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
            create_poi(
                internal_id=item['id'],
                name=item['name'],
                latitude=item['coordinates']['latitude'],
                longitude=item['coordinates']['longitude'],
                category=item['category'],
                ratings=ratings
            )

@shared_task
@transaction.atomic
def process_xml_file(file_path):
    """
    Processes and imports data from an XML file into the PointOfInterest model.

    Args:
        file_path (str): The path to the XML file to process.
    """
    with open(file_path, 'rb') as source:
        content = source.read(32 * 1024 * 1024 + 1)
    if len(content) > 32 * 1024 * 1024 or b'<!DOCTYPE' in content.upper() or b'<!ENTITY' in content.upper():
        raise ValueError('XML must be at most 32 MiB and contain no DTD/entities')
    root = ET.fromstring(content)
    for poi_element in root:
        ratings_str = poi_element.find('pratings').text
        ratings = [float(rating) for rating in ratings_str.split(',')]
        average_rating = sum(ratings) / len(ratings) if ratings else 0
        create_poi(
            internal_id=poi_element.find('pid').text,
            name=poi_element.find('pname').text,
            latitude=float(poi_element.find('platitude').text),
            longitude=float(poi_element.find('plongitude').text),
            category=poi_element.find('pcategory').text,
            ratings=average_rating
        )
