
from datetime import datetime
from hashlib import sha256
from json import dumps
import logging
from base64 import b64encode
from os import getenv
from random import randint
from secrets import token_bytes
from typing import Optional
from functools import lru_cache

from celery import Task
from django.contrib.auth.hashers import make_password
from django.core.cache import cache
from django.db import transaction
from dotenv import load_dotenv
from redis import Redis
from smsaero import SmsAero

from account.models import User
from config.celery import app
from tariff.src.tools import Main

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


@app.task()
def task_create_account(payment_value: float, cache_id: str, payment_id: str) -> None:
    reg_cache_model: RegistrationCacheModel = cache.get(cache_id)
    password = b64encode(token_bytes(9)).decode()
    with transaction.atomic():
        reg_cache_model.user.password = make_password(password)
        reg_cache_model.user.tariff_plan_id = 2
        reg_cache_model.user.next_tariff_plan_id = 1
        reg_cache_model.user.save()
        reg_cache_model.user.tariffs.add(1)
        reg_cache_model.user.tariffs.add(2)
        _main = Main(reg_cache_model.user, payment_id)
        _main.add_balance(payment_value)
        _main.activate()
        reg_cache_model.user.save()


@app.task(name='send_sms_code', bind=True)
def send_sms_code(
            self: Task, phone: int, user_id: int
        ) -> None:
    user = User.objects.get(id=user_id)
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

