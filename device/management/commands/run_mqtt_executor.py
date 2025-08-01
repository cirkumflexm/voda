
import logging

from django.core.management.base import BaseCommand
from django.db import transaction

from account.models import User

logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger(__name__)


class Command(BaseCommand):
    def handle(self, *args, **options):
        from django.db.models import QuerySet, Q
        from device.models import Encoard, Device
        from device.common import CLIENT, mqtt

        def on_connect(*args):
            for model in QuerySet(Device) \
                    .filter(func="GET") \
                    .iterator():
                LOGGER.info(CLIENT.subscribe(
                    f"MX210/{model.name}/GET/DI/MASK"
                ))

        def on_message(client: mqtt.Client, _, msg: mqtt.MQTTMessage, *args) -> None:
            LOGGER.info((msg.topic, msg.payload))
            name, ws_mask = msg.topic.split("/")[1], int(msg.payload, 2)
            encoads = QuerySet(Encoard) \
                .select_related("device") \
                .select_related("user") \
                .filter(device__name=msg.topic.split("/")[1]) \
                .all()
            for encoad in encoads:
                encoad.user.ws_status = (1 << encoad.number & ws_mask) >> encoad.number
            LOGGER.info([_.user for _ in encoads])
            User.objects.bulk_update([_.user for _ in encoads], ('ws_status',))

        CLIENT.on_connect = on_connect
        CLIENT.on_message = on_message

        CLIENT.connect("m3.wqtt.ru", 13297)
        CLIENT.loop_forever()