from assistant.models import Character
from django.contrib.auth import authenticate, login, logout
from django.core.exceptions import ValidationError
from django.http import (
    HttpRequest, 
    HttpResponse, 
    HttpResponseBadRequest, 
    HttpResponseForbidden, 
    HttpResponseRedirect, 
    JsonResponse
)
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST
from datetime import date
from dateutil.relativedelta import relativedelta
from .models import (
    User, 
    Subscription, 
    SubscriptionStatus, 
    SubscriptionOrder, 
    SUBSCRIPTION_PRODUCTS
)
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
        )

        # trial_subscription = Subscription.objects.create(
        #     user=new_user,
        #     expiry_datetime = timezone.now() + relativedelta(days=3)
        # )

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
    
    try:
        subscription = Subscription.objects.get(user_id=request.user.id)
    except Subscription.DoesNotExist:
        subscription = None

    return JsonResponse({
        'id': request.user.id,
        'mobile_phone': request.user.mobile_phone,
        'subscription_status': get_subscription_status(subscription),
        'subscription_expiry_time': get_subscription_expiry_timestamp(subscription),
    })

def get_subscription_status(subscription: Subscription):
    if not subscription:
        return SubscriptionStatus.INACTIVE
    return SubscriptionStatus.ACTIVE if subscription.expiry_datetime > timezone.now() else SubscriptionStatus.INACTIVE
    
def get_subscription_expiry_timestamp(subscription: Subscription):
    if not subscription:
        return None
    return int(subscription.expiry_datetime.timestamp())

@csrf_exempt
@require_POST
def log_out(request: HttpRequest):
    logout(request)
    return HttpResponse()

@require_GET
def pay_for_subscription_alipay(request: HttpRequest):
    if not request.user.is_authenticated:
        return HttpResponseForbidden('Not logged in')

    params = request.GET

    if 'product_id' not in params:
        return HttpResponseBadRequest()

    subscription_product = SUBSCRIPTION_PRODUCTS.get(params['product_id'], None)
    if not subscription_product:
        return HttpResponseBadRequest()

    order_id = payment.generate_order_id(prefix=SubscriptionOrder.ORDER_ID_PREFIX)
    SubscriptionOrder.objects.create(
        order_id=order_id, 
        user=request.user, 
        product_id=params['product_id'],
        amount_str=subscription_product['price'],
        amount=subscription_product['price'],
    )

    form_html = payment.get_alipay_payment_form_desktop_web(
        order_id=order_id, 
        subject=subscription_product['order_product_name'], 
        total_amount=subscription_product['price'],
    )
    return HttpResponse(form_html)

@require_GET
def pay_for_subscription_wechat(request: HttpRequest):
    return HttpResponseBadRequest("Not supported")

@require_GET
def payment_return(request: HttpRequest):
    return HttpResponseRedirect('/#/me')

@csrf_exempt
@require_POST
def payment_callback(request: HttpRequest):
    params = request.POST
    logging.info(f'Alipay notify params: {params}')
    
    if not payment.verify_alipay_notification(params):
        logging.warning(f'Alipay notification verification failed. Alipay notify params: {params}')
        return HttpResponse('fail')

    order_id = params['out_trade_no']
    if order_id.startswith(SubscriptionOrder.ORDER_ID_PREFIX):
        subscription_order = SubscriptionOrder.objects.get(order_id=order_id)
        if subscription_order.paid_datetime:
            logging.warning(f'Order {order_id} was already paid')
            return HttpResponse('success')

        # if subscription_order.amount_str != params['total_amount']:
        #     logging.warning(f'Amount for order ID {order_id} does not match the Alipay order: {params["total_amount"]}')
        #     return HttpResponse('fail')
        subscription_order.paid_datetime = timezone.now()
        subscription_order.save()

        try:
            subscription = Subscription.objects.get(user_id=subscription_order.user.id)
        except Subscription.DoesNotExist:
            subscription = Subscription(user=subscription_order.user)
        
        current_expiry_datetime = subscription.expiry_datetime if subscription.expiry_datetime else subscription_order.paid_datetime
        subscription.expiry_datetime = current_expiry_datetime \
                                       + relativedelta(months=SUBSCRIPTION_PRODUCTS[subscription_order.product_id]['time_months'])
        subscription.save()
    else:
        logging.warning(f'Unrecognized order ID: {order_id}')

    return HttpResponse('success')
