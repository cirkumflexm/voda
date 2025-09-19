import logging

from django.core.cache import cache
from yookassa.domain.response import PaymentResponse
from yookassa.domain.exceptions.not_found_error import NotFoundError
from account.models import User, RegistrationCacheModel
from tariff.src.tools import Main
from config.celery import app
from account.tasks import task_create_account
from .service import *


@app.task(autoretry_for=(AssertionError, ), max_retries=120, default_retry_delay=5)
def check(payment_id: str, user_id: int = None, reg_cache_model_id: str = None) -> float:
    payment = find_payment(payment_id=payment_id)
    assert payment.status == "succeeded", "Оплата не готова."
    if payment.payment_method and payment.payment_method.saved:
        if user_id:
            User.objects.filter(id=user_id).update(payment_method=payment.payment_method.id)
        elif reg_cache_model_id:
            reg_cache_model: RegistrationCacheModel = cache.get(reg_cache_model_id)
            reg_cache_model.user.payment_method = payment.payment_method.id
            cache.set(reg_cache_model_id, reg_cache_model)
    return float(payment.amount.value)


@app.task
def complete(value: float, payment_id: str, user_id: int) -> None:
    user = User.objects.get(id=user_id)
    _main = Main(user, payment_id)
    _main.add_balance(value)
    _main.activate()
    user.save(update_fields=("ws_status", "start_datetime_pp", "end_datetime_pp"))
