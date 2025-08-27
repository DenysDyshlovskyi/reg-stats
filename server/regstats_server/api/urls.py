# All urls for paths starting with /api/
from django.urls import path
from . import views

urlpatterns = [
    path('register', views.register, name="register"),
    path('remove_client', views.remove_client, name="remove_client"),
    path('get_ws_session', views.get_ws_session, name="get_ws_session"),
    path('get_update', views.get_update, name="get_update"),
    path('add_data', views.add_data, name="add_data")
]