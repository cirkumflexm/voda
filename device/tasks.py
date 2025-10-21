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
            .filter(device__func='SET') \
            .values('device_id', 'device__name') \
            .annotate(
                numbers=ArrayAgg('number'),
                ws_status_list=ArrayAgg('address__user__ws_status')
            )
        for definition in definitions:
            pins = [
                number for number, status in
                zip(definition['numbers'], definition['ws_status_list'])
                if status
            ]
            mask = reduce(int.__or__.__call__, pins) if pins else 0
            event = f"MX210/{definition['device__name']}/SET/DO/MASK"
            CLIENT.publish(event, mask)
            logging.info("%s %s", event, bin(mask))
    finally:
        self.retry(countdown=15)

set_ws_s_task.delay()