
import logging
from base64 import b64encode

from os import getenv
from random import randint
from secrets import token_bytes
from time import sleep
from typing import Optional

from celery import Task
from redis import Redis
from smsaero import SmsAero
from dotenv import load_dotenv
from account.models import User

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

api = SmsAero(
    SMSAERO_EMAIL, SMSAERO_API_KEY,
    test_mode=bool(int(SMSAERO_TEST_MODE))
)

create_account: Task

redis = Redis(db=1)

@app.task()
def create_account(
        *, phone: int, email: str,
        first_name: str, last_name: str,
        apartment: str, fias: str, address: str,
        tariff_plan: Optional[int]
) -> None:
    password = b64encode(token_bytes(9)).decode()
    count = User.objects.count() + 1
    personal_account = f'{count + int(START_RANGE_PERSONAL_ID):0>12}'
    message = MESSAGE % (first_name, password)
    redis.lpush("sms_list", f"Sms for {personal_account}\n{message}")
    redis.ltrim("sms_list", 0, 9)
    LOGGER.info(MESSAGE % (first_name, "*" * 9))
    result = api.send_sms(phone, message)
    while True:
        sleep(10)
        result = api.sms_status(result['id'])
        match result['status']:
            case 1:
                user = User.objects.create_user(
                    username=personal_account,
                    email=email,
                    password=password,
                    personal_account=personal_account,
                    phone=phone,
                    last_name=last_name,
                    first_name=first_name,
                    fias=fias,
                    address=address,
                    apartment=apartment,
                    tariff_plan_id=tariff_plan
                )
                user.groups.add(3)
                user.save()
                break
            case 2:
                break
            case 6:
                break
            case _:
                pass


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