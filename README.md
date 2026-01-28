# Carpedia

A Django-based car encyclopedia with data from Autopedia wiki, featuring generation-specific specs and swipeable image galleries.

## Features

- **Car Catalog** - Browse cars in a responsive grid layout
- **Search** - Search by car name or brand
- **Filters** - Filter by brand and year range
- **Car Details** - View full specifications with swipeable image gallery
- **Generation Selector** - Switch between car generations to view different specs
- **Car Comparison** - Compare up to 4 cars side by side
- **Admin Panel** - Manage car entries via Django admin

## Tech Stack

- Python 3.x
- Django 4.2
- SQLite
- IMAGIN.Studio API (car images)
- Autopedia Fandom wiki (car data)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/Dlgvn/carpedia.git
cd carpedia
```

2. Create a virtual environment (optional but recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run migrations:
```bash
python manage.py migrate
```

5. Import car data from Autopedia:
```bash
python manage.py fetch_autopedia
```

6. Create a superuser for admin access:
```bash
python manage.py createsuperuser
```

7. Start the development server:
```bash
python manage.py runserver
```

8. Open http://127.0.0.1:8000/ in your browser

## Project Structure

```
carpedia/
├── manage.py
├── requirements.txt
├── carpedia_project/       # Django project settings
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
└── cars/                   # Main application
    ├── models.py           # Car and Generation models
    ├── views.py            # View logic
    ├── forms.py            # Search and filter forms
    ├── urls.py             # URL routing
    ├── admin.py            # Admin configuration
    ├── templatetags/       # Custom template filters
    │   └── car_extras.py
    ├── management/
    │   └── commands/
    │       └── fetch_autopedia.py  # Data import command
    └── templates/cars/
        ├── base.html
        ├── car_list.html
        ├── car_detail.html
        └── car_compare.html
```

## Data Models

### Car
| Field | Description |
|-------|-------------|
| name | Car model name |
| brand | Manufacturer |
| description | Short description |
| body_style | e.g., SUV, Sedan |
| car_class | e.g., Mid-size luxury |
| production_years | e.g., 2000-present |

### Generation
| Field | Description |
|-------|-------------|
| car | Foreign key to Car |
| name | Generation name |
| code | Generation code (e.g., W210) |
| year_start | Start year |
| year_end | End year |
| engine | Engine specs |
| horsepower | Power output |
| torque | Torque output |
| top_speed | Maximum speed |
| acceleration | 0-60/0-100 time |
| transmission | Transmission type |

## Usage

- **Homepage** (`/`) - View all cars with search and filter options
- **Car Detail** (`/car/<id>/`) - View specs with swipeable gallery and generation selector
- **Compare** (`/compare/`) - Compare selected cars side by side
- **Admin** (`/admin/`) - Add, edit, or delete cars

## Image Gallery

The car detail page features a swipeable image gallery with:
- 7 different viewing angles from IMAGIN.Studio
- Touch/swipe support for mobile devices
- Navigation arrows and dot indicators
- Automatic fallback placeholder if images fail to load

## Data Import

Import car data from Autopedia Fandom wiki:

```bash
# Import all cars
python manage.py fetch_autopedia

# Import limited number for testing
python manage.py fetch_autopedia --limit 50

# Clear existing data and reimport
python manage.py fetch_autopedia --clear
```

## License

MIT
