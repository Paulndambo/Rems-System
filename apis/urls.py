from django.urls import path, include
from .listings.views import UnitListingListView, UnitListingDetailView, CollectListingViewsAPIView, PropertyViewInterestsAPIView, ListingImageListView, ClientRequestsAPIView, ClientRequestDetailAPIView
from apis.views import PaystackWebhookView


urlpatterns = [
    path('listings/', UnitListingListView.as_view()),
    path('listings/<int:id>/', UnitListingDetailView.as_view()),
    path('listings/images/', ListingImageListView.as_view()),
    path('client-requests/', ClientRequestsAPIView.as_view(), name="client-requests"),
    path('property-view-interests/', PropertyViewInterestsAPIView.as_view(), name='property-view-interest'),
    path('collect-listing-views/', CollectListingViewsAPIView.as_view(), name='collect-listing-views'),
    path('client-requests/<int:id>/', ClientRequestDetailAPIView.as_view(), name='client-request-detail'),
    path('paystack-webhook/', PaystackWebhookView.as_view(), name='paystack-webhook'),
]

