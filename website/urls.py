from django.urls import path
from website.views import ListingListView, ListerView, unit_listing_details, approve_listing, reject_listing, new_webiste_listing, mark_amenity_available, mark_amenity_unavailable

urlpatterns = [
    path("", ListingListView.as_view(), name="website-listings"),
    path("<int:pk>/", unit_listing_details, name="listing-details"),
    path("new-listing/", new_webiste_listing, name="new-listing"),
    path("approve-listing/", approve_listing, name="approve-listing"),
    path("decline-listing/", reject_listing, name="decline-listing"),
    path("mark-amenity-available/<int:id>/", mark_amenity_available, name="mark-amenity-available"),
    path("mark-amenity-unavailable/<int:id>/", mark_amenity_unavailable, name="mark-amenity-unavailable"),
    path("listers/", ListerView.as_view(), name="listers"),
]