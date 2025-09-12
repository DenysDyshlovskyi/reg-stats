from django.urls import path, include, re_path
from . import views

urlpatterns = [
    path('', views.index, name="index"),
    path('api/', include('regstats_server.api.urls')),
    # path('wipedata', views.wipedata, name="wipedata"),
    path('add_password', views.add_password, name="add_password"),
    path('change_nickname', views.change_nickname, name="change_nickname")
]