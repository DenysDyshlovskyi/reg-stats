from django.urls import path, include, re_path
from . import views

urlpatterns = [
    path('api/', include('regstats_server.api.urls')),
]