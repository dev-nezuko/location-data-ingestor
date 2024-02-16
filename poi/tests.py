import tempfile
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase

from poi.models import PointOfInterest
from poi.tasks import process_csv_chunk, process_json_file, process_xml_file

FIXTURES = Path(__file__).resolve().parent / 'test_files'
CSV_HEADER = 'poi_id,poi_name,poi_category,poi_latitude,poi_longitude,poi_ratings\n'


class ProcessCSVChunkTests(TestCase):
    def import_csv_text(self, text):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'input.csv'
            path.write_text(text, encoding='utf-8')
            return process_csv_chunk.run(str(path))

    def test_valid_rows_are_imported_with_average_rating(self):
        self.import_csv_text(CSV_HEADER + '1,Test POI 1,Category 1,10.0,20.0,"{5,4,3}"\n'
                             '2,Test POI 2,Category 2,15.0,25.0,"{2,3,4}"\n')
        self.assertEqual(PointOfInterest.objects.count(), 2)
        first = PointOfInterest.objects.get(internal_id='1')
        self.assertEqual((first.name, first.latitude, first.longitude, first.ratings), ('Test POI 1', 10.0, 20.0, 4.0))
        second = PointOfInterest.objects.get(internal_id='2')
        self.assertEqual((second.name, second.latitude, second.longitude), ('Test POI 2', 15.0, 25.0))

    def test_zero_byte_file_imports_nothing(self):
        process_csv_chunk.run(str(FIXTURES / 'empty_data.csv'))
        self.assertEqual(PointOfInterest.objects.count(), 0)

    def test_rows_with_unparseable_values_are_skipped(self):
        with self.assertLogs('poi.tasks', 'WARNING') as logs:
            process_csv_chunk.run(str(FIXTURES / 'invalid_data.csv'))
        self.assertEqual(PointOfInterest.objects.count(), 0)
        self.assertEqual(logs.output, ['WARNING:poi.tasks:Skipping invalid CSV line 2'])

    def test_rows_missing_values_are_skipped(self):
        with self.assertLogs('poi.tasks', 'WARNING'):
            process_csv_chunk.run(str(FIXTURES / 'incomplete_data.csv'))
        self.assertEqual(PointOfInterest.objects.count(), 0)

    def test_blank_name_is_rejected_rather_than_stored_as_nan(self):
        with self.assertLogs('poi.tasks', 'WARNING'):
            self.import_csv_text(CSV_HEADER + '7,,Cafe,1,2,"{4,5}"\n')
        self.assertFalse(PointOfInterest.objects.exists())

    def test_extra_columns_are_ignored(self):
        process_csv_chunk.run(str(FIXTURES / 'extra_column.csv'))
        self.assertEqual(PointOfInterest.objects.get(internal_id='4').name, 'Extra Columns POI')

    def test_malformed_ratings_are_skipped(self):
        with self.assertLogs('poi.tasks', 'WARNING'):
            process_csv_chunk.run(str(FIXTURES / 'malformed_ratings.csv'))
        self.assertEqual(PointOfInterest.objects.count(), 0)

    def test_non_numeric_source_ids_are_kept_like_json_and_xml(self):
        self.import_csv_text(CSV_HEADER + 'cafe-9,Corner cafe,Cafe,1,2,"{4}"\n')
        self.assertEqual(PointOfInterest.objects.get().internal_id, 'cafe-9')

    def test_counts_cover_rows_across_insert_batches(self):
        rows = ''.join(f'{n},Stop {n},bus-stop,1,2,"{{3}}"\n' for n in range(5))
        with patch('poi.tasks.INSERT_BATCH_SIZE', 2), self.assertLogs('poi.tasks', 'WARNING'):
            counts = self.import_csv_text(CSV_HEADER + rows + 'bad,,bus-stop,1,2,"{3}"\n')
        self.assertEqual(counts, {'imported': 5, 'skipped': 1})
        self.assertEqual(PointOfInterest.objects.count(), 5)

    def test_unicode_names_and_trailing_empty_columns(self):
        process_csv_chunk.run(str(FIXTURES / 'dummy.csv'))
        self.assertEqual(PointOfInterest.objects.count(), 10)


class ProcessStructuredFileTests(TestCase):
    def test_json_fixture_is_imported_with_average_rating(self):
        process_json_file.run(str(FIXTURES / 'valid_data.json'))
        self.assertEqual(PointOfInterest.objects.count(), 2)
        first = PointOfInterest.objects.get(internal_id='1')
        self.assertEqual((first.name, first.latitude, first.longitude, first.ratings), ('POI 1', 10.0, 20.0, 4.0))

    def test_empty_json_array_imports_nothing(self):
        process_json_file.run(str(FIXTURES / 'empty.json'))
        self.assertEqual(PointOfInterest.objects.count(), 0)

    def test_xml_fixture_is_imported(self):
        process_xml_file.run(str(FIXTURES / 'valid_data.xml'))
        self.assertEqual(sorted(PointOfInterest.objects.values_list('name', flat=True)), ['POI 1', 'POI 2'])

    def test_empty_xml_fixture_imports_nothing(self):
        process_xml_file.run(str(FIXTURES / 'empty_data.xml'))
        self.assertEqual(PointOfInterest.objects.count(), 0)

    def test_process_xml_file_with_valid_data(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'valid.xml'
            path.write_text('<pois><poi><pid>1</pid><pname>Synthetic park</pname><pcategory>Park</pcategory><platitude>10</platitude><plongitude>20</plongitude><pratings>5,4,3</pratings></poi></pois>')
            process_xml_file(str(path))
        point = PointOfInterest.objects.get(internal_id='1')
        self.assertEqual(point.name, 'Synthetic park')
        self.assertEqual(point.ratings, 4)

    def test_xml_record_missing_a_tag_names_it_and_rolls_back(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'missing.xml'
            path.write_text('<pois><poi><pid>1</pid><pname>Park</pname><pcategory>Park</pcategory>'
                            '<platitude>10</platitude><plongitude>20</plongitude><pratings>4</pratings></poi>'
                            '<poi><pid>2</pid><pname>Pier</pname><platitude>1</platitude>'
                            '<plongitude>2</plongitude><pratings>3</pratings></poi></pois>')
            with self.assertRaisesMessage(ValueError, 'XML record 2 has no <pcategory> value'):
                process_xml_file.run(str(path))
        self.assertFalse(PointOfInterest.objects.exists())


class ImportCommandOutputTests(TestCase):
    def test_sync_import_reports_counts_per_file(self):
        output = StringIO()
        with self.assertLogs('poi.tasks', 'WARNING'):
            call_command('import_poi', str(FIXTURES / 'valid_data.json'), str(FIXTURES / 'invalid_data.csv'),
                         sync=True, stdout=output)
        self.assertEqual(output.getvalue().splitlines(), [
            'valid_data.json: 2 imported, 0 skipped',
            'invalid_data.csv: 0 imported, 1 skipped',
            '2 file(s) processed.',
        ])
