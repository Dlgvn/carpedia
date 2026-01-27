from django.shortcuts import render, get_object_or_404
from django.db.models import Q
from django.core.paginator import Paginator
from .models import Car
from .forms import CarSearchForm, CarFilterForm


def car_list(request):
    cars = Car.objects.all()
    search_form = CarSearchForm(request.GET)
    filter_form = CarFilterForm(request.GET)

    query = request.GET.get('query', '').strip()
    if query:
        cars = cars.filter(
            Q(name__icontains=query) | Q(brand__icontains=query)
        )

    brand = request.GET.get('brand')
    if brand:
        cars = cars.filter(brand=brand)

    year_min = request.GET.get('year_min')
    if year_min:
        cars = cars.filter(year__gte=year_min)

    year_max = request.GET.get('year_max')
    if year_max:
        cars = cars.filter(year__lte=year_max)

    paginator = Paginator(cars, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'search_form': search_form,
        'filter_form': filter_form,
    }
    return render(request, 'cars/car_list.html', context)


def car_detail(request, pk):
    car = get_object_or_404(Car, pk=pk)
    return render(request, 'cars/car_detail.html', {'car': car})


def car_compare(request):
    """Compare up to 4 cars side by side."""
    car_ids_str = request.GET.get('cars', '')
    car_ids = [int(id) for id in car_ids_str.split(',') if id.strip().isdigit()]
    cars = list(Car.objects.filter(pk__in=car_ids)[:4])

    # Define specs to compare with labels
    specs = [
        ('brand', 'Brand'),
        ('year', 'Year'),
        ('generation_code', 'Generation'),
        ('generation_years', 'Production Years'),
        ('engine', 'Engine'),
        ('horsepower', 'Horsepower'),
        ('top_speed', 'Top Speed (km/h)'),
        ('acceleration', '0-100 km/h (s)'),
        ('transmission', 'Transmission'),
        ('fuel_type', 'Fuel Type'),
        ('body_style', 'Body Style'),
        ('price', 'Price (USD)'),
    ]

    context = {
        'cars': cars,
        'specs': specs,
    }
    return render(request, 'cars/car_compare.html', context)
