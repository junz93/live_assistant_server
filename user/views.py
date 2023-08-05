from django.contrib.auth import authenticate, login, logout
from django.core.exceptions import ValidationError
from django.http import HttpRequest, HttpResponse, HttpResponseBadRequest, HttpResponseForbidden, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST
from .models import User

import json

@csrf_exempt
@require_POST
def register(request: HttpRequest):
    try:
        new_uesr_dict = json.loads(request.body)
        mobile_phone = new_uesr_dict.get('mobile_phone')
        password = new_uesr_dict.get('password')
        new_user = User.objects.create_user(
            username=mobile_phone, 
            mobile_phone=mobile_phone, 
            password=password
        )
        
        return JsonResponse({ 'id': new_user.id })
    except (ValidationError, ValueError) as e:
        return HttpResponseBadRequest('Invalid input')

@csrf_exempt
@require_POST
def log_in(request: HttpRequest):
    if request.user.is_authenticated:
        return HttpResponse()
    
    try:
        uesr_dict = json.loads(request.body)
        mobile_phone = uesr_dict.get('mobile_phone')
        password = uesr_dict.get('password')
        user = authenticate(username=mobile_phone, password=password)
        if user is not None:
            login(request, user)
            return HttpResponse()
        else:
            return HttpResponseForbidden('Phone number or password is incorrect')
    except (ValidationError, ValueError) as e:
        return HttpResponseBadRequest('Invalid input')

@require_GET
def get_user_info(request: HttpRequest):
    if not request.user.is_authenticated:
        return HttpResponseForbidden('Not logged in')
    
    return JsonResponse({ 'id': request.user.id, 'mobile_phone': request.user.mobile_phone })

@csrf_exempt
@require_POST
def log_out(request: HttpRequest):
    logout(request)
    return HttpResponse()
