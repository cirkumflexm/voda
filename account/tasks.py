
import logging
from base64 import b64encode

from os import getenv
from random import randint
from secrets import token_bytes
from time import sleep
from typing import Optional

from celery import Task, chain
from celery.signals import worker_ready
from django.core.cache import cache
from django.db import transaction
from redis import Redis
from smsaero import SmsAero
from dotenv import load_dotenv
from yookassa.domain.response import PaymentResponse

from account.models import User, RegistrationCacheModel
from address.models import Address

from config.celery import app
from tariff.models import TariffPlan
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

api = SmsAero(
    SMSAERO_EMAIL, SMSAERO_API_KEY,
    test_mode=bool(int(SMSAERO_TEST_MODE))
)

create_account: Task

redis = Redis(db=1)

@app.task
def task_create_account(payment_value: float, cache_id: str, payment_id: str) -> float:
    reg_cache_model: RegistrationCacheModel = cache.get(cache_id)
    # password = b64encode(token_bytes(9)).decode()
    password = "test"
    with transaction.atomic():
        reg_cache_model.user.password = password
        reg_cache_model.user.tariff_plan.owner_id = 5
        Main(reg_cache_model.user, payment_id).add_balance(payment_value)
        reg_cache_model.user.tariff_plan.save()
        reg_cache_model.user.save()
        reg_cache_model.user.groups.add(3)
        reg_cache_model.user.address.save()
    message = MESSAGE % (reg_cache_model.user.first_name, password)
    redis.lpush("sms_list", f"Sms for {reg_cache_model.user.address.pa}\n{message}")
    redis.ltrim("sms_list", 0, 9)
    LOGGER.info(MESSAGE % (reg_cache_model.user.first_name, "*" * 9))
    # api.send_sms(int(user.phone.replace('+', '')), message)
    return payment_value


@app.task()
def send_sms_code(phone: str, is_user: bool, pa: str) -> tuple[str | None, str]:
    if is_user:
        _rand = randint(100100, 900900)
        message = SMS_MESSAGE % f'{_rand:_}'.replace('_', '-')
        redis.lpush("sms_list", f"Sms to {phone}\n{message}")
        redis.ltrim("sms_list", 0, 9)
        # api.send_sms(user.phone, message)
        return str(_rand), pa
    return None, pa

