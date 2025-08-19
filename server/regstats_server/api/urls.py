# All urls for paths starting with /api/
from django.urls import path
from . import views

urlpatterns = [
    path('register', views.register, name="register"),
    path('remove_client', views.remove_client, name="remove_client"),
    path('get_ws_session', views.get_ws_session, name="get_ws_session")
]