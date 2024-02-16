import json
import tempfile
from pathlib import Path
from unittest.mock import patch
from django.core.management import call_command, CommandError
from django.test import TestCase
from poi.tasks import process_json_file, process_xml_file
from poi.models import PointOfInterest


class ImportSafetyTests(TestCase):
    def test_json_rolls_back_a_file_after_invalid_coordinates(self):
        valid = {'id': 'one', 'name': 'Synthetic park', 'category': 'Park', 'coordinates': {'latitude': 10, 'longitude': 20}, 'ratings': [4, 5]}
        invalid = {**valid, 'id': 'two', 'coordinates': {'latitude': 100, 'longitude': 20}}
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'input.json'
            path.write_text(json.dumps([valid, invalid]))
            with self.assertRaises(ValueError):
                process_json_file.run(str(path))
        self.assertEqual(PointOfInterest.objects.count(), 0)

    def test_nonfinite_rating_is_rejected(self):
        value = {'id': 'one', 'name': 'Synthetic park', 'category': 'Park', 'coordinates': {'latitude': 10, 'longitude': 20}, 'ratings': [float('inf')]}
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'input.json'
            path.write_text(json.dumps([value]))
            with self.assertRaises(ValueError):
                process_json_file.run(str(path))
        self.assertFalse(PointOfInterest.objects.exists())

    def test_xml_dtd_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'input.xml'
            path.write_text('<!DOCTYPE x [<!ENTITY x "expanded">]><pois/>')
            with self.assertRaises(ValueError):
                process_xml_file.run(str(path))

    def test_command_rejects_all_inputs_before_queueing_any(self):
        with tempfile.TemporaryDirectory() as directory, patch('poi.management.commands.import_poi.process_json_file.delay') as queue:
            path = Path(directory) / 'valid.json'
            path.write_text('[]')
            with self.assertRaises(CommandError):
                call_command('import_poi', str(path), str(Path(directory) / 'missing.json'))
            queue.assert_not_called()

    def test_command_queues_absolute_paths_and_supports_sync(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'valid.json'
            path.write_text('[]')
            with patch('poi.management.commands.import_poi.process_json_file.delay') as queue:
                call_command('import_poi', str(path))
                queue.assert_called_once_with(str(path.resolve()))
            with patch('poi.management.commands.import_poi.process_json_file.delay') as queue:
                call_command('import_poi', str(path), sync=True)
                queue.assert_not_called()
