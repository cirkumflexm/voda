from django.core.cache import cache

from account.models import User
from config.celery import app
from tariff.src.tools import Main
from .service import *


@app.task(
    autoretry_for=(AssertionError, ),
    max_retries=120,
    default_retry_delay=5,
    ignore_result=True,
    bind=True
)
def check(self, payment_id: str, user_id: int) -> float:
    payment = find_payment(payment_id=payment_id)
    assert payment.status == "succeeded", "Оплата не готова."
    if payment.payment_method and payment.payment_method.saved:
        User.objects.filter(id=user_id).update(payment_method=payment.payment_method.id)
    return float(payment.amount.value)


@app.task
def complete(value: float, payment_id: str, user_id: int) -> None:
    user = User.objects.get(id=user_id)
    _main = Main(user, payment_id)
    _main.add_balance(value)
    _main.activate()
    user.save(update_fields=("ws_status", "start_datetime_pp", "end_datetime_pp", "balance"))
