import logging
from functools import reduce

from celery import Task
from django.contrib.postgres.aggregates import ArrayAgg
from django.utils import timezone
from requests import get
from requests.auth import HTTPBasicAuth

from config.celery import app
from config.env import NANOMQ_USERNAME, NANOMQ_PASSWORD
from device.models import Definition, Device


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


@app.task(bind=True, ignore_result=True, max_retries=None)
def undefine_device_delete(self: Task) -> None:
    try:
        Device.objects.filter(
                isnot_online__isnull=True, 
                delete_at__lte=timezone.now()
        ).delete()
    finally:
        self.retry(countdown=60)


@app.task(bind=True, ignore_result=True, max_retries=None)
def nanomq_clients(self: Task) -> None:
    try:
        response = get(
                "http://localhost:8081/api/v4/clients",
                auth=HTTPBasicAuth(NANOMQ_USERNAME, NANOMQ_PASSWORD)
        )
        usernames = [
                _['username'] 
                for _ in response.json()['data']
                if _['conn_state'] == 'connected'
        ]
        devices = [*Device.objects.all()]
        for device in devices:
            is_exists = device.username in usernames
            if device.isnot_online is None:
                if is_exists:
                    device.isnot_online = False
                    device.delete_at = None
            else:
                device.isnot_online = not is_exists
        Device.objects.bulk_update(devices, ('isnot_online', 'delete_at'))
    finally:
        self.retry(countdown=5)


# set_ws_s_task.delay()
undefine_device_delete.delay()
nanomq_clients.delay()
