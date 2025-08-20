from django.db.models import Q

from account.models import User
from config.celery import app
from django.utils import timezone
from tariff.src.tools import Main, CustomException


def tariff_activate(user: User):
    try:
        Main(user).activate()
    except CustomException:
        ...


@app.task()
def task_tariff_renewal_loop() -> None:
    for user in User.objects \
            .select_related('tariff', 'next_tariff_plan') \
            .filter(Q(User.end_datetime_pp <= timezone.now())) \
            .iterator():
        user.start_datetime_pp = None
        user.end_datetime_pp = None
        user.ws_status = False
        if user.tariff_plan and user.tariff_plan.is_test:
            user.tariff_plan.archive = True
            user.tariff_plan = None
        if user.next_tariff_plan:
            user.tariff_plan = user.next_tariff_plan
            user.next_tariff_plan = None
        tariff_activate(user)
        user.save()


@app.task()
def task_tariff_activate_loop() -> None:
    for user in User.objects \
            .select_related('tariff') \
            .filter(
                ~Q(User.tariff_plan is None) &
                Q(User.balance - User.tariff_plan.price >= 0)
            ) \
            .iterator():
        tariff_activate(user)
        user.save()
