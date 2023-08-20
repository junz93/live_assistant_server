from datetime import datetime
from zoneinfo import ZoneInfo

def cst_now():
    "Return the current datetime in CST (China Standard Time)."
    return datetime.now(tz=ZoneInfo('Asia/Shanghai'))
