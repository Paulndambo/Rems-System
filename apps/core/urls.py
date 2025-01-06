from django.urls import path
from apps.core.views import home, months, years, new_year, water_prices, activate_year, deactivate_year, edit_water_price

urlpatterns = [
    path('', home, name='home'),
    path('months/', months, name='months'),
    path('years/', years, name='years'),
    path('new-year/', new_year, name='new-year'),
    path('water-prices/', water_prices, name='water-prices'),
    path('edit-water-price/', edit_water_price, name='edit-water-price'),
    path('activate-year/<int:id>/', activate_year, name='activate-year'),
    path('deactivate-year/<int:id>/', deactivate_year, name='deactivate-year'),
]