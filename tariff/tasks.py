
import logging

from celery import Task, group
from celery.signals import worker_ready
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from account.models import User
from config.celery import app
from tariff.src.tools import Main, CustomException


def tariff_activate(user: User) -> None:
    try:
        Main(user).activate()
    except CustomException:
        ...


def set_next_tariff(user: User) -> None:
    if user.next_tariff_plan:
        user.tariff_plan = user.next_tariff_plan
        user.next_tariff_plan = None


def complete_tariff(user: User) -> None:
    user.ws_status = False
    user.end_datetime_pp = None
    user.start_datetime_pp = None


@app.task()
def task_init_payment(*, user: User, **kw) -> tuple[User, dict]:
    return user, kw


@app.task(bind=True, ignore_result=True, max_retries=None)
def task_tariff_activate_loop(self: Task) -> None:
    try:
        with transaction.atomic():
            for user in User.objects \
                    .select_for_update(skip_locked=True) \
                    .filter(
                        Q(end_datetime_pp__lt = timezone.now()) | \
                            Q(end_datetime_pp__isnull=True),
                        groups__id=3,
                        tariff_plan__isnull=False,
                        ws_status=True
                    ) \
                    .only(
                        'balance',
                        'tariff_plan__archive',
                        'tariff_plan__price',
                        'ws_status',
                        'tariff_plan__unit_measurement',
                        'balance',
                        'start_datetime_pp',
                        'end_datetime_pp',
                        'start_datetime_pp',
                        'is_new',
                        'next_tariff_plan',
                    ) \
                    .all()[:10]:
                logging.info(f"user - {user}")
                complete_tariff(user)
                set_next_tariff(user)
                if user.auto_payment:
                    tariff_activate(user)
                user.save()
    finally:
        self.retry(countdown=0)


# @worker_ready.connect
# def startup(*args, **kw) -> None:
#     group(task_tariff_activate_loop.s() for _ in range(1)).apply_async()