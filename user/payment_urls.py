from django.urls import path

from . import views

urlpatterns = [
    path('pay_alipay', views.pay_alipay),
    path('payment_callback', views.payment_callback),
]