import logging

from alipay.aop.api.AlipayClientConfig import AlipayClientConfig
from alipay.aop.api.DefaultAlipayClient import DefaultAlipayClient
from alipay.aop.api.domain.AlipayTradePagePayModel import AlipayTradePagePayModel
from alipay.aop.api.request.AlipayTradePagePayRequest import AlipayTradePagePayRequest
from alipay.aop.api.response.AlipayTradePagePayResponse import AlipayTradePagePayResponse
from config_utils import auth_config
from datetime import datetime, timedelta, timezone
from django.conf import settings

logger = logging.getLogger()

alipay_client_config = AlipayClientConfig(sandbox_debug=settings.DEBUG)
alipay_client_config.app_id = auth_config['alipay']['AppId']
alipay_client_config.app_private_key = auth_config['alipay']['AppPrivateKey']
alipay_client_config.alipay_public_key = auth_config['alipay']['AlipayPublicKey']
alipay_client_config.encrypt_type = 'AES'
alipay_client_config.encrypt_key = auth_config['alipay']['AesEncryptionKey']

alipay_client = DefaultAlipayClient(alipay_client_config, logger)

def desktop_web_pay():
    dt = datetime.now(tz=timezone(timedelta(hours=8)))

    model = AlipayTradePagePayModel()
    model.out_trade_no = dt.strftime('%Y%m%d%H%M%S%f')  # Example: 20230813123540433476

def mobile_web_pay():
    pass
