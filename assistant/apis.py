import time

from .chatgpt import services
from django.http import HttpRequest, HttpResponse, HttpResponseBadRequest, JsonResponse
from django.views.decorators.http import require_GET

@require_GET
def get_answer(request: HttpRequest):
    question = request.GET.get('question', default='')
    if not question.strip():
        return HttpResponseBadRequest('Missing or empty parameter: "question"')
    else:
        if not request.session.session_key:
            request.session.create()
        return JsonResponse({
            'session_id': request.session.session_key, 
            'anwser': services.get_answer(question, request.session.session_key, event_time=int(time.time()))
        }, json_dumps_params={'ensure_ascii': False})
        # return JsonResponse({'anwser': services.get_answer(question)})
