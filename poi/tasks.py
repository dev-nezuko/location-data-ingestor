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

MAX_IMPORT_BYTES = 32 * 1024 * 1024
INSERT_BATCH_SIZE = 1000
CSV_FIELDS = ('poi_id', 'poi_name', 'poi_category', 'poi_latitude', 'poi_longitude', 'poi_ratings')


def build_poi(**values):
    """Return a validated, unsaved PointOfInterest."""
    for field in ('latitude', 'longitude', 'ratings'):
        value = float(values[field])
        if not math.isfinite(value):
            raise ValueError('Coordinates and ratings must be finite')
        values[field] = value
    if not -90 <= values['latitude'] <= 90 or not -180 <= values['longitude'] <= 180:
        raise ValueError('Coordinates outside latitude/longitude bounds')
    point = PointOfInterest(**values)
    point.full_clean()
    return point


def save_points(points):
    PointOfInterest.objects.bulk_create(points, batch_size=INSERT_BATCH_SIZE)
    return len(points)


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
    a missing name being stored as the text "nan". Valid rows are inserted in
    batches; batches already written stay written if a later one fails.
    """
    imported = skipped = 0
    pending = []
    with open(file_path, newline='', encoding='utf-8-sig') as source:
        reader = csv.DictReader(source)
        for row in reader:
            values = {field: (row.get(field) or '').strip() for field in CSV_FIELDS}
            try:
                pending.append(
                    build_poi(
                        internal_id=values['poi_id'],
                        name=values['poi_name'],
                        category=values['poi_category'],
                        latitude=values['poi_latitude'],
                        longitude=values['poi_longitude'],
                        ratings=average_csv_ratings(values['poi_ratings']),
                    )
                )
            except (ValueError, ValidationError):
                skipped += 1
                logger.warning('Skipping invalid CSV line %d', reader.line_num)
            if len(pending) >= INSERT_BATCH_SIZE:
                imported += save_points(pending)
                pending = []
    imported += save_points(pending)
    return {'imported': imported, 'skipped': skipped}


@shared_task
@transaction.atomic
def process_json_file(file_path):
    """Import a JSON array of POIs; any invalid record rolls back the whole file."""
    with open(file_path, encoding='utf-8') as source:
        data = json.load(source)
    points = []
    for item in data:
        ratings = sum(item['ratings']) / len(item['ratings']) if item['ratings'] else 0
        points.append(
            build_poi(
                internal_id=item['id'],
                name=item['name'],
                latitude=item['coordinates']['latitude'],
                longitude=item['coordinates']['longitude'],
                category=item['category'],
                ratings=ratings,
            )
        )
    return {'imported': save_points(points), 'skipped': 0}


def xml_text(element, tag, position):
    child = element.find(tag)
    if child is None or child.text is None:
        raise ValueError(f'XML record {position} has no <{tag}> value')
    return child.text


@shared_task
@transaction.atomic
def process_xml_file(file_path):
    """Import POI child elements of the XML root; any invalid record rolls back the whole file."""
    with open(file_path, 'rb') as source:
        content = source.read(MAX_IMPORT_BYTES + 1)
    if len(content) > MAX_IMPORT_BYTES or b'<!DOCTYPE' in content.upper() or b'<!ENTITY' in content.upper():
        raise ValueError('XML must be at most 32 MiB and contain no DTD/entities')
    points = []
    for position, element in enumerate(ET.fromstring(content), start=1):
        ratings = [float(rating) for rating in xml_text(element, 'pratings', position).split(',')]
        points.append(
            build_poi(
                internal_id=xml_text(element, 'pid', position),
                name=xml_text(element, 'pname', position),
                latitude=xml_text(element, 'platitude', position),
                longitude=xml_text(element, 'plongitude', position),
                category=xml_text(element, 'pcategory', position),
                ratings=sum(ratings) / len(ratings),
            )
        )
    return {'imported': save_points(points), 'skipped': 0}
