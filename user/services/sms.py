from alibabacloud_dysmsapi20170525.client import Client as Dysmsapi20170525Client
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_dysmsapi20170525.models import SendSmsRequest
# from alibabacloud_tea_util import models as util_models
from alibabacloud_tea_util.client import Client as UtilClient

from utils.config import auth_config

import logging
import json


sms_client_config = open_api_models.Config(
    access_key_id=auth_config['aliyun']['AccessKeyId'],
    access_key_secret=auth_config['aliyun']['AccessKeySecret'],
    endpoint='dysmsapi.aliyuncs.com'
)

sms_client = Dysmsapi20170525Client(sms_client_config)


def send_verification_sms(code: str, mobile_phone: str):
    request = SendSmsRequest(
        phone_numbers=mobile_phone,
        sign_name='无色界科技',
        template_code='SMS_285015193',
        template_param=json.dumps({'code': code}),
    )
    try:
        response = sms_client.send_sms(request)
    except Exception as e:
        logging.exception(UtilClient.assert_as_string(e.message))
