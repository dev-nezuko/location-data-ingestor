# Search Smartly

## Description

Search Smartly is a Django web application designed to process and import Point of Interest (PoI) data from various file formats (CSV, JSON, XML) into a local database. The application allows users to browse PoI information via the Django Admin Panel and search for PoIs by internal or external ID, with an additional filter by category.

## Requirements

### Submission Process

After completing the task, please share the project via a git repository. The repository should include:

- A Django web application running on Python 3.10 or above.
- A README.md file explaining installation and usage instructions, including any assumptions made and ideas for improvement.

### Application Requirements

1. **Django Project**: The application should be a Django project running on Python 3.10 or above.

2. **Management Command**: It should have a management command that can be called with the path to a file (or files). The command should extract and store PoI data from each file into a local database.

3. **Django Admin Site**: The application should include a Django admin site displaying the following PoI data:
   - PoI internal ID
   - PoI name
   - PoI external ID
   - PoI category
   - Average rating

4. **Search Functionality**: Users should be able to search for PoIs by internal or external ID.

5. **Filtering**: The application should provide filtering options by PoI category.

### Application Notes

- **Models and Database Schema**: You have the flexibility to design the models and database schema as needed.
- **Local Deployment**: Focus on ensuring the project works locally; no deployment to a remote environment is required.
- **Files Specification**:
  - **CSV**: poi_id, poi_name, poi_latitude, poi_longitude, poi_category, poi_ratings
  - **JSON**: id, name, coordinates[latitude, longitude], category, ratings, description
  - **XML**: pid, pname, platitude, plongitude, pcategory, pratings

## Installation and Usage

### Prerequisites

- Python 3.10 or above
- Django

### Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/yourusername/search-smartly.git
   ```

2. Navigate to the project directory:

   ```bash
   cd search-smartly
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Run database migrations:

   ```bash
   python manage.py migrate
   ```

### Usage

1. Import PoI data from files using the management command:

   ```bash
   python manage.py import_poi <file_path>
   ```

2. Access the Django Admin Panel to browse and search PoI data:

   ```bash
   python manage.py runserver
   ```

   Visit http://localhost:8000/admin/ in your web browser.

## Contributing

Contributions to the project are welcome! If you'd like to contribute, please follow the guidelines outlined in the CONTRIBUTING.md file.

