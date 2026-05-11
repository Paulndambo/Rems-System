import math

from decimal import Decimal

from django.db import transaction


from apps.properties.models import PropertyUnit, WaterBill
from apps.core.models import Month, Year
from apps.payments.models import RentBill, UnitMonthBill


class TenantBillingMixin(object):
    def __init__(self, 
        year: Year, 
        month: Month, 
        previous_reading: float, 
        current_reading: float, 
        unit: PropertyUnit
    ):
        self.year = year
        self.month = month
        self.previous_reading = previous_reading
        self.current_reading = current_reading
        self.unit = unit

    @transaction.atomic
    def generate_bill(self):
        try:
            previous_reading = self.previous_reading
            current_reading = self.current_reading
            unit = self.unit
            year = self.year
            month = self.month

            units_consumed = Decimal(current_reading) - Decimal(previous_reading)
            unit_bill = UnitMonthBill.objects.filter(unit=unit, month=month, year=year).first()
            water_cost = Decimal(unit.water_price) * Decimal(units_consumed)
            water_cost_rounded_off = math.ceil(water_cost)

            if not unit_bill:
                unit_bill = UnitMonthBill.objects.create(
                    unit=unit, 
                    tenant=unit.tenant, 
                    month=month, 
                    year=year,
                    water_amount=water_cost_rounded_off,
                    rent_amount=unit.rent
                )
            else:
                unit_bill.water_amount=water_cost_rounded_off
                unit_bill.rent_amount=unit.rent
                unit_bill.save()

            unit_bill.update_amount_expected()

            water_bill = WaterBill.objects.create(
                unit_bill=unit_bill,
                unit=unit,
                property=unit.property,
                tenant=unit.tenant,
                year=year,
                month=month,
                previous_reading=previous_reading,
                current_reading=current_reading,
                meter_number=unit.water_meter_number,
                units_consumed=units_consumed,
                amount=water_cost_rounded_off,
            )

            RentBill.objects.create(
                unit=unit,
                unit_bill=unit_bill,
                tenant=unit.tenant,
                amount_expected=unit.rent,
                due_date=water_bill.due_date,
                month=month,
                year=year,
            )
            
            return True
        except Exception as e:
            raise e
