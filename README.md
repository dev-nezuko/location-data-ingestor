# Search Smartly

## Description

Search Smartly is a Django web application designed to process and import Point of Interest (PoI) data from various file formats (CSV, JSON, XML) into a local database. The application allows users to browse PoI information via the Django Admin Panel and search for PoIs by internal or external ID, with an additional filter by category.

## Approaches

When faced with the challenge of processing large datasets for importing geographical points of interest (POI) data from various file formats, I meticulously evaluated my options. Our primary goal was to ensure efficient data processing without compromising the application's responsiveness and scalability. After thorough consideration, I opted to integrate Celery into our Django application for several compelling reasons:

### Asynchronous Processing
Celery's capability to execute tasks asynchronously meant that our application could offload intensive data processing operations to background workers. This approach significantly enhances the application's responsiveness by keeping the main execution thread free from blocking operations.

### Scalability
The distributed nature of Celery allows for horizontal scaling by adding more workers or servers to handle increased loads. This feature is essential for managing growing datasets without impacting performance negatively.

### Reliability and Fault Tolerance
With Celery, we gained robust error handling mechanisms, including automatic task retries and result storage. This reliability ensures that temporary disruptions do not result in data loss or inconsistencies, maintaining the integrity of our data processing pipeline.

### Integration with Django
Celery's seamless compatibility with Django's ORM and database connections significantly streamlined the implementation process. This integration allowed us to leverage Django's features effectively while adding powerful asynchronous task processing capabilities to our application.

**Why This Approach?**

Celery addressed all our requirements for an efficient, scalable, and reliable data processing solution. It not only met our immediate needs but also provided a foundation for future growth, ensuring our application remains performant and resilient as data volumes expand.

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

