
import logging
import paho.mqtt.client as mqtt
from django.db.models import QuerySet

from account.models import User
from device.models import Device, Definition

LOGGER = logging.getLogger("mqtt.common")


CLIENT = mqtt.Client()
CLIENT.username_pw_set("u_XXKWLD", "HpaltpYw")


def set_ws_status(user: User, switch: bool) -> None:
    encoard = QuerySet(Definition) \
                .filter(user=user, device__func="SET") \
                .first()
    LOGGER.info(f"MX210/{encoard.device.name}/SET/"
                f"DO{encoard.number}/{int(switch)}")
    CLIENT.publish(f"MX210/{encoard.device.name}/SET/"
                    f"DO{encoard.number}/{int(switch)}")