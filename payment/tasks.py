from time import sleep

from config.celery import app
from django.db.models import QuerySet
from yookassa import Payment

from account.models import User
from tariff.src.tools import Main


@app.task()
def check(payment_id: str, user_id: int) -> None:
    for _ in range(720):
        sleep(5)
        __payment = Payment.find_one(payment_id)
        if __payment.status == "succeeded":
            __user = QuerySet(User).get(id=user_id)
            Main(__user, payment_id). \
                add_balance(float(__payment.amount.value))
            __user.save()
            break