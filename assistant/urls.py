from django.urls import path

from . import apis, views

urlpatterns = [
    path('', views.index, name='index'),
    path('api/answer', apis.get_answer),
]