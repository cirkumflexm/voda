
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    def handle(self, *args, **options):
        from django.db.models import QuerySet, Q
        from mqtt_executor.models import Encoard
        from mqtt_executor.common import CLIENT, mqtt

        def on_connect(cls, *args):
            for model in QuerySet(Encoard) \
                    .select_related("device") \
                    .filter(~Q(device__type="SET")) \
                    .iterator():
                CLIENT.subscribe(
                    f"MX210/{model.device.name}/GET/"
                    f"DI{model.number}/COUNTER"
                )

        def on_message(msg: mqtt.MQTTMessage, *args) -> None:
            QuerySet(Encoard) \
                .select_related("device") \
                .select_related("user") \
                .filter(name=msg.topic.split("/")[1]) \
                .update(ws_status=int(msg.payload, 2))

        CLIENT.on_connect = on_connect
        CLIENT.on_message = on_message

        CLIENT.connect("95.183.8.42", 1883, 1)
        CLIENT.loop_forever()