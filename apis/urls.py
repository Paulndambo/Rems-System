from django.urls import path, include
from .listings.views import UnitListingListView, UnitListingDetailView

urlpatterns = [
    path('listings/', UnitListingListView.as_view()),
    path('listings/<int:id>/', UnitListingDetailView.as_view()),
]

