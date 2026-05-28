
from celery import Task
from django.utils import timezone
from requests import get
from requests.auth import HTTPBasicAuth

from config.celery import app
from config.settings.env import NANOMQ_PASSWORD, NANOMQ_USERNAME
from device.models import Device


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


undefine_device_delete.delay()
nanomq_clients.delay()
