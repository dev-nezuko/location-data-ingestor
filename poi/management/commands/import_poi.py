from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from poi.tasks import process_csv_chunk, process_json_file, process_xml_file


class Command(BaseCommand):
    help = 'Import local CSV, JSON or XML POI files, via Celery or --sync.'

    def add_arguments(self, parser):
        parser.add_argument('files', nargs='+')
        parser.add_argument('--sync', action='store_true', help='Process immediately without a broker')

    def handle(self, *args, **options):
        handlers = {'.csv': process_csv_chunk, '.json': process_json_file, '.xml': process_xml_file}
        jobs = []
        for value in options['files']:
            path = Path(value).expanduser().resolve()
            if path.suffix.lower() not in handlers or not path.is_file():
                raise CommandError('Every input must be an existing CSV, JSON or XML file')
            if path.stat().st_size > 32 * 1024 * 1024:
                raise CommandError('Input files must be at most 32 MiB')
            jobs.append((str(path), handlers[path.suffix.lower()]))
        for path, handler in jobs:
            if options['sync']:
                handler.run(path)
            else:
                handler.delay(path)
        action = 'processed' if options['sync'] else 'submitted to Celery'
        self.stdout.write(self.style.SUCCESS(f'{len(jobs)} file(s) {action}.'))
