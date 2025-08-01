
import logging
import paho.mqtt.client as mqtt
from django.db.models import QuerySet

from account.models import User
from device.models import Device, Encoard

LOGGER = logging.getLogger("mqtt.common")


CLIENT = mqtt.Client()
CLIENT.username_pw_set("u_XXKWLD", "HpaltpYw")


def set_ws_status_on(user: User) -> None:
    encoard = QuerySet(Encoard) \
                .select_related("device") \
                .select_related("user") \
                .filter(user=user, device__func="SET") \
                .get()
    LOGGER.info(f"MX210/{encoard.device.name}/SET/"
                f"DI{encoard.number}/1")
    CLIENT.publish(f"MX210/{encoard.device.name}/SET/"
                    f"DI{encoard.number}/1")