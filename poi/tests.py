from django.test import TestCase
from unittest.mock import patch, MagicMock
from poi.models import PointOfInterest
from poi.tasks import process_csv_chunk

class ProcessCSVChunkTests(TestCase):
    """
    Test suite for the process_csv_chunk task in the poi application.

    This class tests the functionality of the process_csv_chunk task to ensure
    it correctly processes input CSV data and creates PointOfInterest objects in
    the database as expected.
    """

    @patch('poi.tasks.pd.read_csv')
    def test_process_csv_chunk_creates_points_of_interest(self, mock_read_csv):
        """
        Test that the process_csv_chunk task correctly processes CSV data and
        creates the appropriate PointOfInterest objects in the database.

        The test mocks pandas' read_csv function to return a predetermined set of
        data rows, simulating the reading of a CSV file. It then verifies that
        after executing the task, the expected PointOfInterest objects exist in
        the database with the correct attributes.
        """
        # Setup mock CSV data
        mock_csv_data = MagicMock()
        mock_csv_data.iterrows.return_value = iter([
            (0, {'poi_id': '1', 'poi_name': 'Test POI 1', 'poi_category': 'Category 1',
                 'poi_latitude': '10.0', 'poi_longitude': '20.0', 'poi_ratings': '{5,4,3}'}),
            (1, {'poi_id': '2', 'poi_name': 'Test POI 2', 'poi_category': 'Category 2',
                 'poi_latitude': '15.0', 'poi_longitude': '25.0', 'poi_ratings': '{2,3,4}'}),
        ])
        mock_read_csv.return_value = [mock_csv_data]

        # Execute the task
        process_csv_chunk('dummy.csv')

        # Assert
        self.assertEqual(PointOfInterest.objects.count(), 2)
        poi1 = PointOfInterest.objects.get(internal_id=1)
        self.assertEqual(poi1.name, 'Test POI 1')
        self.assertEqual(poi1.latitude, 10.0)
        self.assertEqual(poi1.longitude, 20.0)

        poi2 = PointOfInterest.objects.get(internal_id=2)
        self.assertEqual(poi2.name, 'Test POI 2')
        self.assertEqual(poi2.latitude, 15.0)
        self.assertEqual(poi2.longitude, 25.0)
