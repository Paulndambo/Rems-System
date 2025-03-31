from django.urls import path

from apps.users.views import login_user, logout_user, UserListView, new_user, edit_user, delete_user, change_password

urlpatterns = [
    path('login/', login_user, name='login'),
    path('logout/', logout_user, name='logout'),
    path('', UserListView.as_view(), name='users'),
    path('new-user/', new_user, name='new-user'),
    path('edit-user/', edit_user, name='edit-user'),
    path('delete-user/', delete_user, name='delete-user'),
    path('change-password/<int:id>/', change_password, name='change-password'),
]