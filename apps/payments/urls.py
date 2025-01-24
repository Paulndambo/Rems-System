from django.urls import path
from .views import pay_water_bill, WaterBillPaymentsView, RentPaymentsView, CaretakerRentBillsView, rent_payments_overview, pay_rent, single_receipt, ExpenseView, MonthlyRentBillsView, RentReceiptsView, add_expense, edit_expense, delete_expense, RentBillsView, generate_rent_bill

urlpatterns = [
    path("pay-water-bill/", pay_water_bill, name="pay-water-bill"),
    path("water-bill-payments/", WaterBillPaymentsView.as_view(), name="water-bill-payments"),
    path("expenses/", ExpenseView.as_view(), name="expenses"),
    path("new-expense/", add_expense, name="new-expense"),
    path("edit-expense/", edit_expense, name="edit-expense"),
    path("delete-expense/", delete_expense, name="delete-expense"),
    path("rent-bills/<int:month_id>/", RentBillsView.as_view(), name="rent-bills"),
    path("generate-rent-bills/", generate_rent_bill, name="generate-rent-bills"),
    path("monthly-rent-bills/", MonthlyRentBillsView.as_view(), name="monthly-rent-bills"),
    path("rent-receipts/<int:month_id>/", RentReceiptsView.as_view(), name="rent-receipts"),
    path("rent-receipt/<int:rent_receipt_id>/", single_receipt, name="rent-receipt"),
    path("pay-rent-bill/", pay_rent, name="pay-rent-bill"),
    path("rent-payments/", RentPaymentsView.as_view(), name="rent-payments"),
    path("rent-payments-overview/", rent_payments_overview, name="rent-payments-overview"),
    path("caretaker-rent-bills/", CaretakerRentBillsView.as_view(), name="caretaker-rent-bills"),
]