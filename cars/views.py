from django.shortcuts import render, get_object_or_404
from django.db.models import Q
from django.core.paginator import Paginator
from .models import Car, Generation
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
    year_max = request.GET.get('year_max')
    if year_min or year_max:
        # Filter by generation years
        gen_filter = Q()
        if year_min:
            gen_filter &= Q(generations__year_start__gte=year_min) | Q(generations__year_end__gte=year_min)
        if year_max:
            gen_filter &= Q(generations__year_start__lte=year_max)
        cars = cars.filter(gen_filter).distinct()

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
    generations = car.generations.all()

    # Get selected generation (default to first/newest)
    gen_id = request.GET.get('gen')
    if gen_id:
        selected_gen = generations.filter(pk=gen_id).first()
    else:
        selected_gen = generations.first()

    # Get gallery images for selected generation or car
    if selected_gen:
        gallery_images = selected_gen.get_gallery_images()
    else:
        gallery_images = car.get_gallery_images()

    context = {
        'car': car,
        'generations': generations,
        'selected_gen': selected_gen,
        'gallery_images': gallery_images,
    }
    return render(request, 'cars/car_detail.html', context)


def car_compare(request):
    """Compare up to 4 cars side by side."""
    car_ids_str = request.GET.get('cars', '')
    car_ids = [int(id) for id in car_ids_str.split(',') if id.strip().isdigit()]
    cars = list(Car.objects.filter(pk__in=car_ids).prefetch_related('generations')[:4])

    # Get first generation specs for each car
    cars_with_specs = []
    for car in cars:
        gen = car.generations.first()
        cars_with_specs.append({
            'car': car,
            'gen': gen,
        })

    # Define specs to compare with labels
    specs = [
        ('brand', 'Brand', 'car'),
        ('body_style', 'Body Style', 'car'),
        ('car_class', 'Class', 'car'),
        ('production_years', 'Production', 'car'),
        ('engine', 'Engine', 'gen'),
        ('horsepower', 'Horsepower', 'gen'),
        ('torque', 'Torque', 'gen'),
        ('top_speed', 'Top Speed', 'gen'),
        ('acceleration', '0-60 / 0-100', 'gen'),
        ('transmission', 'Transmission', 'gen'),
    ]

    context = {
        'cars_with_specs': cars_with_specs,
        'specs': specs,
    }
    return render(request, 'cars/car_compare.html', context)
