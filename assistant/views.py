from django.core.exceptions import ValidationError
from django.http import HttpRequest, HttpResponse, HttpResponseBadRequest, HttpResponseForbidden, HttpResponseNotFound, Http404, JsonResponse
from django.shortcuts import render, get_object_or_404
# from django.template.context_processors import csrf
from django.middleware import csrf
from django.views.decorators.http import require_GET, require_POST

from .models import Character, Script
from .services import gpt
from utils.userauth import check_usage_limit

import json
import logging
import time


@require_GET
def danmu_interaction(request: HttpRequest):
    return render(request, 'assistant/danmu_interaction.html', {})


@require_GET
def get_csrf_token(request: HttpRequest):
    return JsonResponse({
        'token': csrf.get_token(request),
    })


@check_usage_limit
@require_POST
def create_character(request: HttpRequest):
    try:
        character_dict: dict = json.loads(request.body)
        character = Character.from_dict(character_dict, request.user)
        character.full_clean()
        character.save()
        return JsonResponse({'id': character.id})
    except (ValidationError, ValueError) as e:
        return HttpResponseBadRequest('Invalid input')


@check_usage_limit
@require_POST
def update_character(request: HttpRequest, id: int):
    try:
        character_dict: dict = json.loads(request.body)
        character = Character.objects.get(id=id, user_id=request.user.id)
        character.copy_from_dict(character_dict)
        character.full_clean()
        character.save()
        return HttpResponse()
    except (ValidationError, ValueError) as e:
        # logging.error(exc_info=True)
        return HttpResponseBadRequest('Invalid input')
    except Character.DoesNotExist:
        return HttpResponseNotFound(f'Cannot find a character with ID {id}')


@check_usage_limit
@require_POST
def delete_character(request: HttpRequest, id: int):
    Character.objects.filter(id=id, user_id=request.user.id).delete()
    return HttpResponse()


@check_usage_limit
@require_GET
def get_character(request: HttpRequest, id: int):
    try:
        character = Character.objects.get(id=id, user_id=request.user.id)
        return JsonResponse(character.to_dict(), json_dumps_params={'ensure_ascii': False})
    except Character.DoesNotExist:
        return HttpResponseNotFound(f'Cannot find a character with ID {id}')


@check_usage_limit
@require_GET
def get_all_characters(request: HttpRequest):
    characters = [character.to_dict() for character in Character.objects.filter(user_id=request.user.id)]
    return JsonResponse(characters, safe=False, json_dumps_params={'ensure_ascii': False})


@check_usage_limit
@require_GET
def generate_answer_as_character(request: HttpRequest, character_id: int):
    question = request.GET.get('question', default='')
    if not question.strip():
        return HttpResponseBadRequest('Missing or empty parameter: "question"')
    
    try:
        character = Character.objects.get(id=character_id, user_id=request.user.id)
        response = {
            'answer': ''.join(gpt.get_answer(
                question, 
                f'user_{request.user.id}', 
                int(time.time()), 
                with_censorship=False, 
                character=character,
                mode=gpt.AnswerMode.CHAT,
            ))
        }

        return JsonResponse(response, json_dumps_params={'ensure_ascii': False})
    except Character.DoesNotExist:
        return HttpResponseNotFound(f'Cannot find a character with ID {character_id}')


@check_usage_limit
@require_GET
def generate_script_as_character(request: HttpRequest, character_id: int):
    description = request.GET.get('description', default='')
    if not description.strip():
        return HttpResponseBadRequest('Missing or empty parameter: "description"')
    
    try:
        character = Character.objects.get(id=character_id, user_id=request.user.id)
        response = {
            'script': ''.join(gpt.get_answer(
                description, 
                None,
                int(time.time()),
                with_censorship=False, 
                character=character,
                mode=gpt.AnswerMode.SCRIPT,
            ))
        }

        return JsonResponse(response, json_dumps_params={'ensure_ascii': False})
    except Character.DoesNotExist:
        return HttpResponseNotFound(f'Cannot find a character with ID {character_id}')


@check_usage_limit
@require_POST
def create_script(request: HttpRequest):
    try:
        script_dict: dict = json.loads(request.body)
        script = Script.from_dict(script_dict, request.user)
        script.full_clean()
        script.save()
        return JsonResponse({'id': script.id})
    except (ValidationError, ValueError) as e:
        return HttpResponseBadRequest('Invalid input')


@check_usage_limit
@require_POST
def update_script(request: HttpRequest, id: int):
    try:
        script_dict: dict = json.loads(request.body)
        script = Script.objects.get(id=id, user_id=request.user.id)
        script.copy_from_dict(script_dict)
        script.full_clean()
        script.save()
        return HttpResponse()
    except (ValidationError, ValueError) as e:
        # logging.error(exc_info=True)
        return HttpResponseBadRequest('Invalid input')
    except Script.DoesNotExist:
        return HttpResponseNotFound(f'Cannot find a script with ID {id}')


@check_usage_limit
@require_POST
def delete_script(request: HttpRequest, id: int):
    Script.objects.filter(id=id, user_id=request.user.id).delete()
    return HttpResponse()


@check_usage_limit
@require_GET
def get_script(request: HttpRequest, id: int):
    try:
        script = Script.objects.get(id=id, user_id=request.user.id)
        return JsonResponse(script.to_dict(), json_dumps_params={'ensure_ascii': False})
    except Script.DoesNotExist:
        return HttpResponseNotFound(f'Cannot find a script with ID {id}')


@check_usage_limit
@require_GET
def get_all_scripts(request: HttpRequest):
    scripts = [script.to_dict() for script in Script.objects.filter(user_id=request.user.id)]
    return JsonResponse(scripts, safe=False, json_dumps_params={'ensure_ascii': False})
