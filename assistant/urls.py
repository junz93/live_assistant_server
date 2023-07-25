from django.urls import path

from . import apis, views

urlpatterns = [
    path('', views.index, name='index'),
    path('character/create', views.create_character, name='create_character'),
    path('character/<int:id>/update', views.update_character, name='update_character'),
    path('character/<int:id>/overview', views.character_overview, name='character_overview'),
    path('danmu_interaction', views.danmu_interaction, name='danmu_interaction'),
    path('api/answer', apis.get_answer),
]