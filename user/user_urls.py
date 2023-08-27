from django.urls import path

from . import views

urlpatterns = [
    path('register', views.register),
    path('login', views.log_in),
    path('info', views.get_user_info),
    path('logout', views.log_out),
    path('usage', views.get_usage_info),
    path('record_usage', views.record_usage),
    path('send_verification_sms', views.send_verification_sms),
    path('verify_sms_code', views.verify_sms_code),
]