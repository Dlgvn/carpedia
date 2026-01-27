from django.urls import path
from . import views

app_name = 'cars'

urlpatterns = [
    path('', views.car_list, name='car_list'),
    path('car/<int:pk>/', views.car_detail, name='car_detail'),
    path('compare/', views.car_compare, name='car_compare'),
]
