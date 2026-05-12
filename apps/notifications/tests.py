from django.test import TestCase

from apps.notifications.message_templates import (
    format_bill_payment_message,
    format_garbage_bill_message,
    format_rent_bill_message,
    format_unit_bill_message,
    format_water_bill_message,
)


class MessageTemplateTests(TestCase):
    def test_payment_specific_templates_include_tenant_amount_and_bill_type(self):
        cases = [
            (format_water_bill_message, "water bill payment"),
            (format_rent_bill_message, "rent bill payment"),
            (format_garbage_bill_message, "garbage bill payment"),
        ]

        for formatter, expected_text in cases:
            with self.subTest(formatter=formatter.__name__):
                message = formatter("Test Tenant", 500)
                self.assertIn("*Test Tenant*", message)
                self.assertIn("*500*", message)
                self.assertIn(expected_text, message)

    def test_unit_bill_message_mentions_month_and_year(self):
        message = format_unit_bill_message("Test Tenant", "May", "2026")

        self.assertIn("*Test Tenant*", message)
        self.assertIn("*May, 2026*", message)
        self.assertIn("fully paid", message)

    def test_bill_payment_message_includes_component_amounts_and_total(self):
        message = format_bill_payment_message(
            tenant_name="Test Tenant",
            rent_amount=1000,
            garbage_amount=130,
            water_amount=250,
        )

        self.assertIn("*Test Tenant*", message)
        self.assertIn("Rent Amount: *1000*", message)
        self.assertIn("Garbage Amount: *130*", message)
        self.assertIn("Water Amount: *250*", message)
        self.assertIn("Total Amount: *1380*", message)
