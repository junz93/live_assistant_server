from assistant.models import Character
from django.contrib.auth import authenticate, login, logout
from django.core.exceptions import ValidationError
from django.http import HttpRequest, HttpResponse, HttpResponseBadRequest, HttpResponseForbidden, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST
from datetime import date
from .models import User
from .services import payment

import logging
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
            password=password,
            birth_date=date
        )

        # TODO: decouple the default character creation from register endpoint
        default_character_a = Character(
            user=new_user, 
            name='小博',
            gender='M',
            role='KNOWLEDGE',
            topic='商业与创业',
            birth_date=date.fromisoformat('1988-01-23'),
            education='DOCTOR',
            hobby='博览群书',
            advantage='熟悉公司创业、经营、管理、人力、财务等领域具有多年经验和知识',
            speaking_style='严谨，擅长冷幽默',
            audience_type='20-35岁的创业者',
            personal_statement='商业首席观察官，有任何有关创业投资、企业经营管理的问题，都可以提问'
        )

        default_character_b = Character(
            user=new_user, 
            name='小朵',
            gender='F',
            role='SALE',
            topic='AIGC课程',
            birth_date=date.fromisoformat('1988-01-23'),
            education='DOCTOR',
            advantage='熟悉AI人工智能技术，AIGC，分享AI实用技巧',
            audience_type='职场打工人、创作者',
            personal_statement='AI课程导师，希望能够成为大家学习的助手和伙伴，让每个人都能轻松学习和应用人工智能，并从中受益'
        )

        Character.objects.bulk_create([default_character_a, default_character_b])
        
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

def pay_alipay(request: HttpRequest):
    form_html = payment.desktop_web_pay()
    return HttpResponse(form_html)

@csrf_exempt
@require_POST
def payment_callback(request: HttpRequest):
    params = request.POST
    logging.info(f'Alipay notify params: {params}')
    logging.info(f'Signature verify result: {payment.verify_alipay_signature(params)}')
    return HttpResponse('success')
