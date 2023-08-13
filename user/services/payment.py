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

def desktop_web_pay():
    dt = datetime.now(tz=timezone(timedelta(hours=8)))

    model = AlipayTradePagePayModel()
    model.out_trade_no = dt.strftime('%Y%m%d%H%M%S%f')  # Example: 20230813123540433476
    model.subject = '主播AI助手 一个月会员'
    model.total_amount = '50.23'
    model.product_code = 'FAST_INSTANT_TRADE_PAY'

    request = AlipayTradePagePayRequest(model)
    request.notify_url = 'http://47.103.50.65/api/payment/payment_callback'
    request.need_encrypt = True

    try:
        form_html = alipay_client.page_execute(request)
        return form_html
    except Exception as e:
        logging.exception('Failed to call Alipay')

def mobile_web_pay():
    pass

def verify_alipay_signature(params: QueryDict):
    # params = dict(params)
    params = params.copy()

    if 'sign' not in params:
        return False
    
    signature = params['sign']
    del params['sign']
    if 'sign_type' in params:
        del params['sign_type']

    signed_str = '&'.join(f'{item[0]}={item[1]}' for item in sorted(params.items()))
    logging.info(f'Signed string: {signed_str}')
    
    return verify_with_rsa(alipay_client_config.alipay_public_key, signed_str.encode('utf-8'), signature)
