from django.urls import path, include
from .listings.views import UnitListingListView, UnitListingDetailView, ListingImageListView

urlpatterns = [
    path('listings/', UnitListingListView.as_view()),
    path('listings/<int:id>/', UnitListingDetailView.as_view()),
    path('listings/images/', ListingImageListView.as_view()),
]

