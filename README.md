# Carpedia

A Django-based car catalog website featuring search, filtering, and detailed car specifications.

## Features

- **Car Catalog** - Browse cars in a responsive grid layout
- **Search** - Search by car name or brand
- **Filters** - Filter by brand, year range, and price range
- **Car Details** - View full specifications for each car
- **Admin Panel** - Manage car entries via Django admin

## Tech Stack

- Python 3.x
- Django 4.2
- SQLite
- Pillow (image handling)

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

5. Create a superuser for admin access:
```bash
python manage.py createsuperuser
```

6. Start the development server:
```bash
python manage.py runserver
```

7. Open http://127.0.0.1:8000/ in your browser

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
    ├── models.py           # Car data model
    ├── views.py            # View logic
    ├── forms.py            # Search and filter forms
    ├── urls.py             # URL routing
    ├── admin.py            # Admin configuration
    └── templates/cars/
        ├── base.html
        ├── car_list.html
        └── car_detail.html
```

## Car Model Fields

| Field | Description |
|-------|-------------|
| name | Car model name |
| brand | Manufacturer |
| year | Production year |
| description | Short description |
| engine | Engine type/specs |
| horsepower | Power output (HP) |
| top_speed | Maximum speed (km/h) |
| acceleration | 0-100 km/h time (seconds) |
| price | MSRP in USD |
| image | Car photo |

## Usage

- **Homepage** (`/`) - View all cars with search and filter options
- **Car Detail** (`/car/<id>/`) - View full specifications
- **Admin** (`/admin/`) - Add, edit, or delete cars

## Adding Cars

1. Go to `/admin/` and log in
2. Click on "Cars" under the CARS section
3. Click "Add Car" and fill in the details
4. Upload an image (optional)
5. Save

## License

MIT
