from django.urls import path, include, re_path
from . import views

urlpatterns = [
    path('', views.index, name="index"),
    path('api/', include('regstats_server.api.urls')),
]