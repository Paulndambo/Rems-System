import csv
from decimal import Decimal
from datetime import datetime, timedelta
from apps.properties.models import WaterBill
from apps.properties.models import PropertyUnit
from apps.tenants.models import Tenant
from apps.payments.models import UnitMonthBill, RentBill, GarbageBill
from apps.core.models import Month, Year

from django.db import transaction


def construct_date(date_str):
    split_date = date_str.split("/")
    return datetime(int(split_date[2]), int(split_date[0]), int(split_date[1]))


@transaction.atomic
def load_water_bills():
    water_bills = []

    with open("water_meter_readings.csv", "r") as file:
        water_bills = list(csv.DictReader(file))

    for water_bill in water_bills:
        unit_number = water_bill.get("unit_number")
        unit = PropertyUnit.objects.filter(name=unit_number).first()
        year_str = water_bill.get("year")
        month_str = water_bill.get("month")

        month = Month.objects.filter(name=month_str, year__name=year_str).first()
        if not month:
            print(f"Month {month_str} {year_str} not found")
            continue

        reading_date = construct_date(water_bill.get("reading_date"))
        due_date = reading_date + timedelta(days=5)

        units_consumed = Decimal(water_bill.get("units_consumed"))
        current_reading = Decimal(water_bill.get("current_reading"))
        previous_reading = Decimal(water_bill.get("previous_reading"))

        month_bill = UnitMonthBill.objects.create(
            unit=unit,
            month=month,
            year=month.year,
            rent_amount=unit.rent,
            tenant=unit.tenant,
        )

        wb_bill = WaterBill.objects.create(
            unit_bill=month_bill,
            property=unit.property,
            unit=unit,
            tenant=unit.tenant,
            reading_date=reading_date,
            due_date=due_date,
            month=month,
            year=month.year,
            previous_reading=previous_reading,
            current_reading=current_reading,
            units_consumed=units_consumed,
        )
        wb_bill.amount = wb_bill.total_amount()
        wb_bill.save()

        RentBill.objects.create(
            unit=unit,
            unit_bill=month_bill,
            tenant=unit.tenant,
            amount_expected=unit.rent,
            due_date=due_date,
            month=month,
            year=month.year,
        )

        if str(year_str) == "2025":
            gb = GarbageBill.objects.create(
                unit=unit,
                unit_bill=month_bill,
                tenant=unit.tenant,
                amount_expected=unit.property.garbage_charge,
                due_date=due_date,
            )

            month_bill.garbage_amount = gb.amount_expected
            month_bill.save()

        month_bill.water_amount = wb_bill.amount
        month_bill.save()
        month_bill.update_amount_expected()
        month_bill.save()

        print(f"Unit: {unit_number}")
