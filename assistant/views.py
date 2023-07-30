from django.core.exceptions import ValidationError
from django.http import HttpRequest, HttpResponse, HttpResponseBadRequest, HttpResponseNotFound, Http404, JsonResponse
from django.shortcuts import render, get_object_or_404
# from django.template.context_processors import csrf
from django.middleware import csrf
from django.views.decorators.http import require_GET, require_POST
from .models import Character

import json
import logging

def index(request: HttpRequest):
    return render(request, 'assistant/character.html', {})

@require_GET
def danmu_interaction(request: HttpRequest):
    return render(request, 'assistant/danmu_interaction.html', {})

@require_GET
def get_csrf_token(request: HttpRequest):
    return JsonResponse({
        'token': csrf.get_token(request),
    })

@require_POST
def create_character(request: HttpRequest):
    try:
        character_dict: dict = json.loads(request.body)
        character = Character.from_dict(character_dict)
        character.full_clean()
        character.save()
        return JsonResponse({'id': character.id})
    except (ValidationError, ValueError) as e:
        return HttpResponseBadRequest('Invalid input')

@require_POST
def update_character(request: HttpRequest, id: int):
    try:
        character_dict: dict = json.loads(request.body)
        character = Character.objects.get(id=id)
        character.copy_from_dict(character_dict)
        character.full_clean()
        character.save()
        return HttpResponse()
    except (ValidationError, ValueError) as e:
        # logging.error(exc_info=True)
        return HttpResponseBadRequest('Invalid input')
    except Character.DoesNotExist:
        return HttpResponseNotFound(f'Character with ID {id} does not exist')
    
@require_POST
def delete_character(request: HttpRequest, id: int):
    Character.objects.filter(id=id).delete()
    return HttpResponse()

@require_GET
def get_character(request: HttpRequest, id: int):
    try:
        character = Character.objects.get(id=id)
        return JsonResponse(character.to_dict(), json_dumps_params={'ensure_ascii': False})
    except Character.DoesNotExist:
        return HttpResponseNotFound(f'Character with ID {id} does not exist')

@require_GET
def get_all_characters(request: HttpRequest):
    characters = [character.to_dict() for character in Character.objects.all()]
    return JsonResponse(characters, safe=False, json_dumps_params={'ensure_ascii': False})
