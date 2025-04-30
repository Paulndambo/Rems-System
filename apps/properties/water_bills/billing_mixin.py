import math

from decimal import Decimal

from django.db import transaction


from apps.properties.models import PropertyUnit, WaterBill
from apps.core.models import Month, Year
from apps.payments.models import RentBill, UnitMonthBill, GarbageBill
from apps.core.constants import MONTHS_LIST, PAYMENT_METHODS


class TenantBillingMixin(object):
    def __init__(self, year, month, previous_reading, current_reading, unit):
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

            water_cost = (Decimal(unit.water_price) * Decimal(units_consumed))
            water_cost_rounded_off = math.ceil(water_cost)

            if not unit_bill:
                unit_bill = UnitMonthBill.objects.create(
                    unit=unit,
                    tenant=unit.tenant,
                    month=month,
                    year=year
                )

            unit_bill.water_amount = water_cost_rounded_off
            unit_bill.update_amount_expected()
            unit_bill.save()

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
                amount=water_cost_rounded_off
            )
            
            rent_bill = RentBill.objects.filter(unit=unit, unit_bill=unit_bill).first()
            if not rent_bill:
                RentBill.objects.create(
                    unit=unit,
                    unit_bill=unit_bill,
                    tenant=unit.tenant,
                    amount_expected=unit.rent,
                    due_date=water_bill.due_date,
                    month=month,
                    year=year
                )

            unit_bill.update_amount_expected()
            unit_bill.save()

            garbage_bill = GarbageBill.objects.filter(unit=unit, unit_bill=unit_bill).first()
            if not garbage_bill:
                GarbageBill.objects.create(
                    unit=unit,
                    unit_bill=unit_bill,
                    tenant=unit.tenant,
                    amount_expected=unit.property.garbage_charge,
                    due_date=water_bill.due_date,
                )

            unit_bill.rent_amount = unit.rent
            unit_bill.garbage_amount = unit.property.garbage_charge   
            unit_bill.update_amount_expected()
            unit_bill.save()
            return True
        except Exception as e:
            raise e
