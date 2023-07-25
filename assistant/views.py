from django.http import HttpRequest, HttpResponse, HttpResponseBadRequest, Http404, JsonResponse
from django.shortcuts import render, get_object_or_404
from django.views.decorators.http import require_GET, require_POST
from .models import Character, CharacterForm

def index(request: HttpRequest):
    return HttpResponse('Hello, world')

@require_GET
def danmu_interaction(request: HttpRequest):
    return render(request, 'assistant/danmu_interaction.html', {})

def create_character(request: HttpRequest):
    if request.method == 'POST':
        character_form = CharacterForm(request.POST)
        if character_form.is_valid():
            character_form.save()
            return HttpResponse('Succeeded!')
        else:
            return HttpResponseBadRequest('Invalid input')
    else:
        character_form = CharacterForm()
        return render(request, 'assistant/character.html', {'form': character_form})
    

def update_character(request: HttpRequest, id: int):
    try:
        character = Character.objects.get(id=id)
        if request.method == 'POST':
            character_form = CharacterForm(request.POST, instance=character)
            if character_form.is_valid():
                character_form.save()
                return HttpResponse('Succeeded!')
            else:
                return HttpResponseBadRequest('Invalid input')
        else:
            # character = Character.objects.get(id=id)
            character_form = CharacterForm(instance=character)
            return render(request, 'assistant/character.html', {'form': character_form})
    except Character.DoesNotExist:
        raise Http404(f'Character with ID {id} does not exist')

def character_overview(request: HttpRequest, id: int):
    return HttpResponse('TODO')

# def get_character(request: HttpRequest, id: int):
#     try:
#         character = Character.objects.get(id=id)
#         character_dict = {
#             'id': character.pk,
#             'name': character.name,
#             'gender': character.gender,
#         }
#         return JsonResponse(character, json_dumps_params={'ensure_ascii': False})
#     except Character.DoesNotExist:
#         raise Http404(f'Character with ID {id} does not exist')
