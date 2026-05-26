
import logging
from datetime import datetime
from functools import lru_cache
from hashlib import sha256
from json import dumps
from os import getenv
from random import randint

from celery import Task
from dotenv import load_dotenv
from redis import Redis
from smsaero import SmsAero

from config.celery import app

load_dotenv()

logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger(__name__)

SMSAERO_EMAIL = getenv("SMSAERO_EMAIL")
SMSAERO_API_KEY = getenv("SMSAERO_API_KEY")
SMSAERO_TEST_MODE = getenv("SMSAERO_TEST_MODE")
START_RANGE_PERSONAL_ID = getenv("START_RANGE_PERSONAL_ID")

MESSAGE = """
Здравствуйте, %s! Регистрация прошла успешно.
Пароль: %s
"""

SMS_MESSAGE = """
Код подтверждения: %s
"""


@lru_cache(1)
def get_sms_aero():
    return SmsAero(
        email=SMSAERO_EMAIL,
        api_key=SMSAERO_API_KEY,
        test_mode=bool(int(SMSAERO_TEST_MODE))
    )


@lru_cache(1)
def get_redis():
    return Redis()


@app.task(name='send_sms_code', bind=True)
def send_sms_code(
            self: Task, phone: int, user_id: int
        ) -> None:
    redis = get_redis()
    code = randint(100100, 900900)
    message = SMS_MESSAGE % f'{code:_}'.replace('_', '-')
    code = sha256(str(code).encode()).hexdigest()
    redis.set(
        f'code:{self.request.id}:{code}',
        dumps({
            'user_id': user_id,
            'phone': phone,
            'dttm': datetime.now().isoformat()
        }),
        ex=300
    )
    redis.lpush("sms_list", f"Sms to {phone}\n{message}")
    redis.ltrim("sms_list", 0, 9)
    # api.send_sms(user.phone, message)

