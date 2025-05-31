from django.urls import path

from . import views

urlpatterns = [
    path("", views.clients, name="clients"),
    path("tour-clients/", views.TourClientsListView.as_view(), name="tour-clients"),
    path("new-tour-client/", views.new_tour_client, name="new-tour-client"),
    path("edit-tour-client/", views.edit_tour_client, name="edit-tour-client"),
    path("delete-tour-client/", views.delete_tour_client, name="delete-tour-client"),
    path("birthday-messages/", views.BirthdayMessagesListView.as_view(), name="birthday-messages"),
    
    path("holiday-messages/", views.HolidayMessagesListView.as_view(), name="holiday-messages"),
    path("delete-message/", views.delete_message, name="delete-message"),
    path("new-message/", views.new_message, name="new-message"),
    
    path("upcoming-birthdays/", views.UpcomingBirthdaysView.as_view(), name="upcoming-birthdays"),
]
