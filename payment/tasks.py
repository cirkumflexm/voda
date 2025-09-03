from django.core.cache import cache
from yookassa.domain.response import PaymentResponse
from yookassa.domain.exceptions.not_found_error import NotFoundError
from account.models import User, RegistrationCacheModel
from tariff.src.tools import Main
from config.celery import app
from account.tasks import task_create_account
from .service import *


@app.task(autoretry_for=(AssertionError, ), max_retries=120, default_retry_delay=5)
def check(payment_id: str) -> float:
    payment = find_payment(payment_id=payment_id)
    assert payment.status == "succeeded", "Оплата не готова."
    return float(payment.amount.value)


@app.task
def complete(value: float, payment_id: str, cache_id: str) -> None:
    reg_cache_model: RegistrationCacheModel = cache.get(cache_id)
    Main(reg_cache_model.user, payment_id).add_balance(value)
    reg_cache_model.user.save()
    cache.delete(cache_id)
