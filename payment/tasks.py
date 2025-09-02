from django.core.cache import cache
from yookassa.domain.response import PaymentResponse

from config.celery import app
from yookassa import Payment

from account.models import User, RegistrationCacheModel
from tariff.src.tools import Main


@app.task(autoretry_for=(AssertionError,), max_retries=120, countdown=5)
def check(payment_id: str, cache_id: str) -> tuple[User, PaymentResponse]:
    reg_cache_model: RegistrationCacheModel = cache.get(cache_id)
    payment = Payment.find_one(payment_id)
    assert payment.status == "succeeded", "Оплата не готова."
    return reg_cache_model.user, payment


@app.task()
def complete(user: User, payment: PaymentResponse, payment_id: str) -> User:
    Main(user, payment_id). \
        add_balance(float(payment.amount.value))
    user.save()
    return user
