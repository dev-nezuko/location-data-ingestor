from django.core.management.base import BaseCommand
from poi.tasks import process_csv_chunk, process_json_file, process_xml_file

class Command(BaseCommand):
    """
    A Django management command to import Point of Interest (PoI) data from CSV, JSON, and XML files.

    This command reads files specified as command line arguments and enqueues tasks to process each file
    according to its format. Supported file formats are CSV, JSON, and XML.
    """

    help = 'Import PoI data from CSV, JSON, and XML files.'

    def add_arguments(self, parser):
        """
        Adds command-line arguments to the command.

        Args:
            parser: The command line argument parser instance.
        """
        parser.add_argument('files', nargs='+', type=str, help='List of file paths to import.')

    def handle(self, *args, **options):
        """
        Handles the command execution.

        Iterates over each file path provided as an argument and enqueues a corresponding task
        based on the file's extension.

        Args:
            *args: Variable length argument list.
            **options: Arbitrary keyword arguments.
        """
        for file_path in options['files']:
            if file_path.endswith('.csv'):
                process_csv_chunk.delay(file_path)
            elif file_path.endswith('.json'):
                process_json_file.delay(file_path)
            elif file_path.endswith('.xml'):
                process_xml_file.delay(file_path)

        self.stdout.write(self.style.SUCCESS('All files have been queued for import.'))
