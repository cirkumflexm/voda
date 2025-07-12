
import logging

from os import getenv
from time import sleep
from celery import Task
from smsaero import SmsAero
from dotenv import load_dotenv
from string import ascii_letters, digits, ascii_uppercase
from django.contrib.auth.hashers import make_password
from random import choices, shuffle
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

create_account: Task

@app.task()
def create_account(phone: int, email: str, first_name: str, last_name: str) -> None:
    api = SmsAero(
        SMSAERO_EMAIL, SMSAERO_API_KEY,
        test_mode=bool(int(SMSAERO_TEST_MODE))
    )
    __letters = choices(ascii_letters, k=4)
    __uppercase = choices(ascii_uppercase, k=4)
    __digits = choices(digits, k=4)
    __password = __letters + __uppercase + __digits + [*'%@$%^*']
    shuffle(__password)
    password = "".join(__password[:12])
    count = User.objects.count() + 1
    personal_account = f'{count + int(START_RANGE_PERSONAL_ID):0>12}'
    message = MESSAGE % (first_name, password)
    LOGGER.info(MESSAGE % (first_name, "*" * 12))
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
                    tariff_plan_id=1
                )
                user.groups.add(3)
                break
            case 2:
                break
            case 6:
                break
            case _:
                pass
