from django.urls import path, include
from .listings.views import UnitListingListView, UnitListingDetailView, CollectListingViewsAPIView, ExpressInterestAPIView, ListingImageListView, SubmitClientRequestAPIView

urlpatterns = [
    path('listings/', UnitListingListView.as_view()),
    path('listings/<int:id>/', UnitListingDetailView.as_view()),
    path('listings/images/', ListingImageListView.as_view()),
    path('submit-client-request/', SubmitClientRequestAPIView.as_view(), name="submit-client-request"),
    path('express-interest/', ExpressInterestAPIView.as_view(), name='express-interest'),
    path('collect-listing-views/', CollectListingViewsAPIView.as_view(), name='collect-listing-views'),
]

