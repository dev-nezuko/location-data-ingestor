# Location data ingestor

Import point-of-interest records from CSV, JSON or XML into Django/SQLite, then browse them in Django Admin by source ID, generated ID and category. CSV is read in 1,000-row chunks; JSON and XML are whole-file imports. Each record stores an average of its supplied ratings, not a separate review table.

The original `SearchSmartly` package and [upstream project context](https://github.com/dev-nezuko/location-data-ingestor) are retained. This repository is a file-import exercise, not a public location-search API or geospatial search engine.

## Start with the synchronous path

Use Python 3.11+ in an isolated environment:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
export DEBUG=true
python manage.py migrate
python manage.py import_poi --sync poi/test_files/valid_data.json
python manage.py createsuperuser
python manage.py runserver 127.0.0.1:8000
```

Open `/admin/` with your own local superuser. The initial POI migration is included, so setup does not require generating schema files. No credentials or database are bundled. `DEBUG=true` permits a process-local random signing key; configure a private `SECRET_KEY` in the environment for persistent sessions or any non-debug use. `ALLOWED_HOSTS` defaults to local hosts.

## Queue instead of blocking

To use RabbitMQ/Celery, make input files available at the **same absolute paths on the worker host**:

```sh
export CELERY_BROKER_URL='amqp://guest:guest@127.0.0.1//'
celery -A SearchSmartly worker --loglevel=info
# In a separate configured terminal:
python manage.py import_poi poi/test_files/valid_data.json
```

The broker URL above is the conventional local-only demo account; provision private broker credentials for any shared setup. Celery eager mode defaults to false. `--sync` bypasses the broker explicitly; `CELERY_TASK_ALWAYS_EAGER=true` is available for deliberate eager execution.

The command validates every path/extension before submitting any file, resolves paths absolutely, and accepts files up to 32 MiB. It reports submission, not background completion. Dispatching several files is not a broker transaction; a later dispatch failure can leave earlier jobs queued.

## Data formats

| Format | Required fields |
| --- | --- |
| CSV | `poi_id`, `poi_name`, `poi_category`, `poi_latitude`, `poi_longitude`, `poi_ratings` |
| JSON array | `id`, `name`, `category`, `coordinates.latitude`, `coordinates.longitude`, `ratings` |
| XML child elements | `pid`, `pname`, `pcategory`, `platitude`, `plongitude`, `pratings` |

For example:

```json
[
  {"id":"demo-1","name":"Synthetic park","category":"Park",
   "coordinates":{"latitude":10,"longitude":20},"ratings":[5,4,3]}
]
```

This creates a source ID of `demo-1` and average rating `4`. JSON/XML source IDs remain strings; the legacy CSV parser expects an integer-like `poi_id`. CSV ratings use a quoted brace-delimited field such as `"{5,4,3}"`; XML ratings are comma-separated text.

Coordinates must be finite and within latitude/longitude bounds; average ratings must be finite. Model validation also checks required values and field lengths. Invalid CSV rows are skipped with row-index-only messages; database failures propagate. JSON/XML imports run in one transaction per file, so an invalid record rolls that file back. XML DTD/entity declarations are rejected.

```mermaid
flowchart LR
  F[Validate local file paths] --> M{Execution mode}
  M -->|--sync| I[Format-specific importer]
  M -->|Celery| Q[Broker then shared-path worker]
  Q --> I
  I --> V[Validate fields and average ratings]
  V --> D[(SQLite POI records)]
  D --> A[Django Admin search and category filter]
```

## Checks and practical limits

```sh
DEBUG=true python manage.py test poi
DEBUG=true python manage.py makemigrations --check --dry-run
```

Fifteen tests pass with temporary SQLite databases: importer mapping, real XML parsing, finite values, JSON rollback, DTD rejection, command validation, absolute queued paths and synchronous execution. Migration drift checks pass. Verification used Django 5.2/Pandas 2.2/Celery 5.6 from an existing isolated environment, rather than installing the full legacy pinned environment. No live RabbitMQ worker or background completion was tested.

Imports append rows: `internal_id` is not unique and repeat imports are not idempotent. CSV is chunked but inserts one row at a time; JSON/XML retain the whole file and a transaction in memory. There are no configured automatic retries, persistent job-progress records, dead-letter handling or result-store guarantees. Those need design and tests before claims of reliable large-scale ingestion. A useful next step is a persistent import summary with accepted/rejected counts and an explicit duplicate policy, followed by measured batch-insert performance.
