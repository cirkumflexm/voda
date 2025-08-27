
from yookassa.domain.response import PaymentResponse

from config.celery import app
from yookassa import Payment

from account.models import User
from tariff.src.tools import Main


@app.task(autoretry_for=(AssertionError,), max_retries=120, countdown=5)
def check(payment_id: str, user: User) -> tuple[User, PaymentResponse]:
    payment = Payment.find_one(payment_id)
    assert payment.status == "succeeded", "Оплата не готова."
    return user, payment


@app.task()
def complete(user: User, payment: PaymentResponse, payment_id: str) -> User:
    Main(user, payment_id). \
        add_balance(float(payment.amount.value))
    user.save()
    return user
