from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from poi.tasks import MAX_IMPORT_BYTES, process_csv_chunk, process_json_file, process_xml_file


class Command(BaseCommand):
    help = 'Import local CSV, JSON or XML POI files, via Celery or --sync.'

    def add_arguments(self, parser):
        parser.add_argument('files', nargs='+')
        parser.add_argument('--sync', action='store_true', help='Process immediately without a broker')

    def handle(self, *args, **options):
        handlers = {'.csv': process_csv_chunk, '.json': process_json_file, '.xml': process_xml_file}
        jobs = []
        # Validate every input before dispatching any, so a typo cannot leave a partial batch queued.
        for value in options['files']:
            path = Path(value).expanduser().resolve()
            if path.suffix.lower() not in handlers or not path.is_file():
                raise CommandError('Every input must be an existing CSV, JSON or XML file')
            if path.stat().st_size > MAX_IMPORT_BYTES:
                raise CommandError('Input files must be at most 32 MiB')
            jobs.append((path, handlers[path.suffix.lower()]))
        for path, handler in jobs:
            if options['sync']:
                counts = handler.run(str(path))
                self.stdout.write(f'{path.name}: {counts["imported"]} imported, {counts["skipped"]} skipped')
            else:
                handler.delay(str(path))
        action = 'processed' if options['sync'] else 'submitted to Celery'
        self.stdout.write(self.style.SUCCESS(f'{len(jobs)} file(s) {action}.'))
