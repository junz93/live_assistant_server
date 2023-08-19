import base64
import logging

from alipay.aop.api.AlipayClientConfig import AlipayClientConfig
from alipay.aop.api.DefaultAlipayClient import DefaultAlipayClient
from alipay.aop.api.domain.AlipayTradePagePayModel import AlipayTradePagePayModel
from alipay.aop.api.request.AlipayTradePagePayRequest import AlipayTradePagePayRequest
from alipay.aop.api.response.AlipayTradePagePayResponse import AlipayTradePagePayResponse
from alipay.aop.api.util.SignatureUtils import verify_with_rsa
from config_utils import auth_config
from datetime import datetime, timedelta, timezone
from django.conf import settings
from django.http.request import QueryDict

logger = logging.getLogger()

alipay_config_dict = auth_config['alipay-sandbox' if settings.DEBUG else 'alipay']
alipay_client_config = AlipayClientConfig()
alipay_client_config.app_id = alipay_config_dict['AppId']
alipay_client_config.app_private_key = alipay_config_dict['AppPrivateKey']
alipay_client_config.alipay_public_key = alipay_config_dict['AlipayPublicKey']
alipay_client_config.encrypt_type = 'AES'
alipay_client_config.encrypt_key = alipay_config_dict['AesEncryptionKey']
if settings.DEBUG:
    alipay_client_config.server_url = 'https://openapi-sandbox.dl.alipaydev.com/gateway.do'

alipay_client = DefaultAlipayClient(alipay_client_config, logger)

def generate_order_id(prefix=''):
    dt = datetime.now(tz=timezone(timedelta(hours=8)))
    # TODO: add some random digits to the end
    return dt.strftime(f'{prefix}%Y%m%d%H%M%S%f')

def get_alipay_payment_form_desktop_web(order_id: str, subject: str, total_amount: str):
    model = AlipayTradePagePayModel()
    model.out_trade_no = order_id  # Example: 20230813123540433476
    model.subject = subject
    model.total_amount = total_amount
    model.product_code = 'FAST_INSTANT_TRADE_PAY'

    request = AlipayTradePagePayRequest(model)
    request.notify_url = 'http://assistant.wusejietech.com/api/payment/payment_callback'
    request.return_url = 'http://assistant.wusejietech.com/api/payment/payment_return'
    request.need_encrypt = True

    try:
        form_html = alipay_client.page_execute(request)
        return form_html
    except Exception as e:
        logging.exception('Failed to call Alipay')

# def mobile_web_pay():
#     pass

def verify_alipay_notification(params: QueryDict):
    # params = dict(params)
    params = params.copy()

    if 'sign' not in params \
        or 'seller_id' not in params \
        or 'app_id' not in params:
        return False
    
    if params['seller_id'] != alipay_config_dict['SellerId'] \
        or params['app_id'] != alipay_config_dict['AppId']:
        return False
    
    signature = params['sign']
    del params['sign']
    if 'sign_type' in params:
        del params['sign_type']

    signed_str = '&'.join(f'{item[0]}={item[1]}' for item in sorted(params.items()))
    logging.info(f'Signed string: {signed_str}')
    
    return verify_with_rsa(alipay_client_config.alipay_public_key, signed_str.encode('utf-8'), signature)
