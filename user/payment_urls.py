from django.urls import path

from . import views

urlpatterns = [
    path('subscription/pay_alipay', views.pay_for_subscription_alipay),
    path('subscription/pay_wechat', views.pay_for_subscription_wechat),
    path('payment_return', views.payment_return),
    path('payment_callback', views.payment_callback),
]