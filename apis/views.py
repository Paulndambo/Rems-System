from django.shortcuts import render

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import PaymentRecord, Customer

# Create your views here.
class PaystackWebhookView(APIView):
    def post(self, request, *args, **kwargs):
        data = request.data
        
        # Extract important information from webhook data
        webhook_data = {}
        if data.get('event') == 'charge.success':
            payment_data = data.get('data', {})
            webhook_data = {
                'payment_status': payment_data.get('status'),
                'reference': payment_data.get('reference'),
                'amount': payment_data.get('amount'),
                'currency': payment_data.get('currency'),
                'payment_channel': payment_data.get('channel'),
                'paid_at': payment_data.get('paid_at'),
               
                'listing_id': payment_data.get('metadata', {}).get('listing_id'),
                'request_type': payment_data.get('metadata', {}).get('request_type'),
                'preferred_contact': payment_data.get('metadata', {}).get('preferred_contact'),
                
                # Customer information
                'customer': {
                    'first_name': payment_data.get('customer', {}).get('first_name'),
                    'last_name': payment_data.get('customer', {}).get('last_name'),
                    'email': payment_data.get('customer', {}).get('email'),
                    'phone': payment_data.get('customer', {}).get('phone'),
                },
                
                # Payment method details
                'payment_method': {
                    'bank': payment_data.get('authorization', {}).get('bank'),
                    'channel': payment_data.get('authorization', {}).get('channel'),
                    'country_code': payment_data.get('authorization', {}).get('country_code'),
                }
            }

            customer = Customer.objects.create(
                first_name=webhook_data['customer']['first_name'],
                last_name=webhook_data['customer']['last_name'],
                email=webhook_data['customer']['email'],
                phone=webhook_data['customer']['phone'],
            )

            PaymentRecord.objects.create(
                amount=webhook_data['amount'],
                currency=webhook_data['currency'],
                payment_channel=webhook_data['payment_channel'],
                paid_at=webhook_data['paid_at'],
                reference=webhook_data['reference'],
                customer=customer,
                listing_id=webhook_data['listing_id'],
                request_type=webhook_data['request_type'],
                preferred_contact=webhook_data['preferred_contact'],
                bank=webhook_data['payment_method']['bank'],
                country_code=webhook_data['payment_method']['country_code'],
                payment_status=webhook_data['payment_status'],
            )

            
            print("Processed webhook data:", webhook_data)
        
        return Response(webhook_data, status=status.HTTP_200_OK)
