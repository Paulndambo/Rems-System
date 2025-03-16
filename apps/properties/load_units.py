import csv
from apps.properties.models import Property, PropertyUnit

def determine_unit_floor(unit_name):
    if 'A' in unit_name:
        return '1'
    elif 'B' in unit_name:
        return '2'
    else:
        return '3'


def load_units():
    property = Property.objects.first()
    units = []
    with open('units.csv', 'r') as file:
        units = list(csv.DictReader(file))
    

    for unit in units:
        PropertyUnit.objects.create(
            property=property,
            name=unit['name'],
            rent=unit['rent'],
            security_deposit=unit['security_deposit'],
            unit_type=unit['unit_type'],
            water_price=unit['water_price'],
            floor=determine_unit_floor(unit['name']),
            status="Vacant"
        )

