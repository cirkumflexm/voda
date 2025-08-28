
import logging
from base64 import b64encode

from os import getenv
from random import randint
from secrets import token_bytes
from time import sleep
from typing import Optional

from celery import Task, chain
from celery.signals import worker_ready
from django.db import transaction
from redis import Redis
from smsaero import SmsAero
from dotenv import load_dotenv
from yookassa.domain.response import PaymentResponse

from account.models import User
from address.models import Address

from config.celery import app
from tariff.models import TariffPlan

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

@app.task()
def task_create_account(user: User, payment: PaymentResponse, address: Address) -> tuple[User, PaymentResponse]:
    # password = b64encode(token_bytes(9)).decode()
    password = "test"
    with transaction.atomic():
        user.password = password
        user.groups.add(3)
        user.tariff_plan.save()
        address.save()
        user.save()
    message = MESSAGE % (user.first_name, password)
    redis.lpush("sms_list", f"Sms for {address.pa}\n{message}")
    redis.ltrim("sms_list", 0, 9)
    LOGGER.info(MESSAGE % (user.first_name, "*" * 9))
    # api.send_sms(int(user.phone.replace('+', '')), message)
    return user, payment


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

