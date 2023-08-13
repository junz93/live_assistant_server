from django.urls import path

from . import views

urlpatterns = [
    path('register', views.register),
    path('login', views.log_in),
    path('info', views.get_user_info),
    path('logout', views.log_out),
]