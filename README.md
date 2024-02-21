# Search Smartly

## Description

Search Smartly is a Django web application designed to process and import Point of Interest (PoI) data from various file formats (CSV, JSON, XML) into a local database. The application allows users to browse PoI information via the Django Admin Panel and search for PoIs by internal or external ID, with an additional filter by category.


### Prerequisites
- Python 3.10 or above
- Django

## Installation and Usage


### Dependencies
  ```bash
   1- celery==5.1.2
   2- pandas==2.2.0
   3- RabbitMQ (It is being used as a Message Broker)
   ```
### Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/yourusername/search-smartly.git
   ```

2. Navigate to the project directory:

   ```bash
   cd search-smartly
   ```

3. Install virtual environment and activate it

    ```bash
   python -m venv env
   ```

   ```bash
   source env/bin/activate
   ```

5. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

6. Run database migrations:

   ```bash
   python manage.py makemigrations
   ```
   
   ```bash
   python manage.py migrate
   ```

### Usage

1. Start Celery:
   ```bash
   celery -A SearchSmartly worker --loglevel=info
   ```
     
2. Import PoI data from files using the management command:

   ```bash
   python3 manage.py import_poi <file_path>
   ```

3. Access the Django Admin Panel to browse and search PoI data:

   ```bash
   python3 manage.py runserver
   ```

   Visit http://localhost:8000/admin/ in your web browser.

### Usage

Test Cases:
```bash
python3 manage.py test poi.tests
```


### Looks Like
 <img width="1619" alt="image" src="https://github.com/dev-nezuko/location-data-ingestor/assets/119432487/d7c79baa-166b-4d89-8267-7a69c755aa78">

## Contributing

Contributions to the project are welcome! If you'd like to contribute, please follow the guidelines outlined in the CONTRIBUTING.md file.

