import requests
from django.conf import settings
class WhatsAppNotification:
    def __init__(self, message: str, recipient: str = "254745491093"):
        self.message = message
        self.phone_number = recipient
        self.instance_key = settings.WAAPI_TESTING_INSTANCE_KEY# WAAPI_INSTANCE_KEY
        self.api_key = settings.WAAPI_TESTING_API_KEY #WAAPI_API_KEY

    def send_message(self):
        """Send WhatsApp message using WaAPI."""
        url = f'https://waapi.app/api/v1/instances/{self.instance_key}/client/action/send-message'
        
        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "authorization": f"Bearer {self.api_key}"
        }
        
        payload = {
            "chatId": f"{self.phone_number}@c.us",
            "message": self.message
        }
        
        response = requests.post(url, json=payload, headers=headers)
        return response.json() if response.content else {}
