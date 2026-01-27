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

    price_min = request.GET.get('price_min')
    if price_min:
        cars = cars.filter(price__gte=price_min)

    price_max = request.GET.get('price_max')
    if price_max:
        cars = cars.filter(price__lte=price_max)

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
