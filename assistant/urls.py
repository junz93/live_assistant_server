from django.urls import path

from . import apis, views

urlpatterns = [
    path('', views.index, name='index'),
    path('csrf_token', views.get_csrf_token),
    path('danmu_interaction', views.danmu_interaction, name='danmu_interaction'),
    path('character/all', views.get_all_characters, name='get_all_characters'),
    path('character/<int:id>', views.get_character, name='get_character'),
    path('character/create', views.create_character, name='create_character'),
    path('character/<int:id>/update', views.update_character, name='update_character'),
    path('character/<int:id>/delete', views.delete_character, name='delete_character'),
    path('api/answer', apis.get_answer),
]