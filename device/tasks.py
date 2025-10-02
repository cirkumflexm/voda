import logging
from functools import reduce

from celery import Task
from celery.signals import worker_ready
from django.contrib.postgres.aggregates import ArrayAgg

from account.models import User
from config.celery import app
from device.common import CLIENT
from device.models import Definition


@app.task(bind=True, ignore_result=True, max_retries=None)
def set_ws_s_task(self: Task) -> None:
    try:
        definitions = Definition.objects \
            .filter(
                device__func='SET',
                user__ws_status=True
            ) \
            .values('device_id', 'device__name') \
            .annotate(numbers=ArrayAgg('number'))
        for definition in definitions:
            mask = reduce(int.__or__.__call__, (0b11 << (_ - 1) * 2 for _ in definition['numbers']))
            event = f"MX210/{definition['device__name']}/SET/DO/MASK"
            CLIENT.publish(event, mask)
            logging.info("%s %s", event, mask)
    finally:
        self.retry(countdown=15)


@worker_ready.connect
def startup(*args, **kw) -> None:
    set_ws_s_task.delay()