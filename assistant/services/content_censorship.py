from alibabacloud_green20220302.client import Client
from alibabacloud_green20220302 import models
from alibabacloud_tea_openapi.models import Config
# from alibabacloud_tea_util.client import Client as UtilClient
# from alibabacloud_tea_util import models as util_models
from live_assistant.config_utils import auth_config

import json
import logging
import uuid

config = Config(
    access_key_id=auth_config['aliyun']['AccessKeyId'],
    access_key_secret=auth_config['aliyun']['AccessKeySecret'],
    # 连接时超时时间，单位毫秒（ms）。
    connect_timeout=3000,
    # 读取时超时时间，单位毫秒（ms）。
    read_timeout=3000,
    # 接入区域和地址请根据实际情况修改。
    region_id='cn-beijing',
    endpoint='green-cip.cn-beijing.aliyuncs.com',
)
client = Client(config)

# Returns True if text content is safe
def check_text(text: str):
    if not text:
        logging.warning('Empty text')
        return False
    service_parameters = {
        'content': text,
        'dataId': str(uuid.uuid4())
    }
    request = models.TextModerationRequest(
        service = 'comment_detection',
        service_parameters = json.dumps(service_parameters)
    )
    try:
        response = client.text_moderation(request)
        if not response or response.status_code != 200 or not response.body or response.body.code != 200:
            logging.error(f'Failed response: {response}')
            return True
        else:
            if response.body.data.labels:
                logging.warning(f'Unsafe content detected in text "{text}". Labels: {response.body.data.labels}. Reason: {response.body.data.reason}')
                return False
            return True
    except Exception as e:
        logging.error(f'Encountered errors when checking text "{text}". Errors: {e}')
        return True

