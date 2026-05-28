

from functools import lru_cache

import paho.mqtt.client as mqtt

from config.settings.env import NANOMQ_PASSWORD, NANOMQ_USERNAME
from device.models import Definition


@lru_cache(1)
def get_client():
    client = mqtt.Client()
    client.username_pw_set(NANOMQ_USERNAME, NANOMQ_PASSWORD)
    client.connect(host="95.183.8.42", port=1883)
    return client


def set_ws_status(pa: int, switch: bool) -> None:
    defination = Definition.objects \
            .select_related('device') \
            .values('device__name', 'port') \
            .get(address_id=pa)
    client = get_client()
    client.publish(
        f'MX210/{defination['device__name']}'
        f'/SET/DO{defination['port']}/{int(switch)}'
    )
