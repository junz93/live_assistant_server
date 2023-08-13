from django.urls import path

from . import apis, views

urlpatterns = [
    path('csrf_token', views.get_csrf_token),
    path('danmu_interaction', views.danmu_interaction, name='danmu_interaction'),
    path('character/all', views.get_all_characters, name='get_all_characters'),
    path('character/<int:id>', views.get_character, name='get_character'),
    path('character/create', views.create_character, name='create_character'),
    path('character/<int:id>/update', views.update_character, name='update_character'),
    path('character/<int:id>/delete', views.delete_character, name='delete_character'),
    path('character/<int:character_id>/generate_answer', views.generate_answer_as_character),
    path('character/<int:character_id>/generate_script', views.generate_script_as_character),
    path('script/all', views.get_all_scripts),
    path('script/<int:id>', views.get_script),
    path('script/create', views.create_script),
    path('script/<int:id>/update', views.update_script),
    path('script/<int:id>/delete', views.delete_script),
    path('api/answer', apis.get_answer),
    path('answer', apis.get_answer),
]