import requests
from apps.payments.models import UnitMonthBill
from toursclients.models import TourClient, Message

TIARA_CONNECT_URL = 'https://api2.tiaraconnect.io/api/messaging/sendsms'
TIARA_API_KEY = "eyJhbGciOiJIUzUxMiJ9.eyJzdWIiOiI1NTIiLCJvaWQiOjU1MiwidWlkIjoiM2JjOWU5ZTMtNjVjYy00OGE1LWIyMTMtZDNjMjJmMTNiYmMzIiwiYXBpZCI6NTI1LCJpYXQiOjE3NDUzMTIwMTQsImV4cCI6MjA4NTMxMjAxNH0.8zDf2REJFDoPO8gdQ1t9OAv73I6_OX1GWHJpAQ6eVXkQyuuSt5Q4IEIxLatkfhFVm6vs8utnVd4WpfkPJmbEOw"


def rent_reminder_template(bill: UnitMonthBill):
    total_unit_bills = sum(list(UnitMonthBill.objects.filter(tenant=bill.tenant).exclude(id=bill.id).values_list("amount_expected", flat=True)))
    total_unit_bills_paid = sum(list(UnitMonthBill.objects.filter(tenant=bill.tenant, fully_paid=True).exclude(id=bill.id).values_list("amount_paid", flat=True)))
    total_unit_bills_pending = total_unit_bills - total_unit_bills_paid
    return f"""
Hello {bill.tenant.user.first_name},
Here is your bill for: {bill.month.name},
Current Month Rent: {bill.rent_amount},
Current Month Water Bill: {bill.water_amount}
Unpaid Dues: {total_unit_bills_pending}
Total Amount: {total_unit_bills_pending + bill.amount_expected}
"""


def birthday_message_template(client: TourClient):
    return f"""
Hello {client.name},
Hope you are doing well.
Happy birthday {client.name}!
"""

def holiday_message_template(message: Message, client: TourClient):
    return f"""
Hello {client.name},
Hope you are doing well.
Happy {message.holiday_name}!
"""



class TiaraConnectSMSManager:
    def __init__(self, phone_number, message):
        self.phone_number = phone_number
        self.message = message
        
    def run(self):
        self.__send_sms(message=self.message)
        
    def __send_sms(self, message):
        phone_number = self.__clean_phone_number(self.phone_number)

        headers = {
            'Authorization': f'Bearer {TIARA_API_KEY}',
            'Content-Type': 'application/json'
        }
        data = {
            "from": "CONNECT",
            "to": self.phone_number,
            "message": message,
        }
        print(f"Phone number is: {phone_number}")

        response = requests.post(TIARA_CONNECT_URL, headers=headers, json=data)

        print(response.status_code)
        print(response.json())


    def __clean_phone_number(self, phone_number):

        if phone_number[0] in ["0", 0]:
            return f"254{phone_number[1:]}"
        elif phone_number[0] in ["+"]:
            return f"{phone_number[1:]}"
        else:
            return phone_number

    def send_rent_reminder(self, bill):
        message = rent_reminder_template(bill)
        print("*******************Message********************")
        print(message)
        self.__send_sms(message=message)
        print("*******************Message********************")
        
        