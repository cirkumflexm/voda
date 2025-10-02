import logging
from functools import reduce
from os import environ

from django.contrib.postgres.aggregates import ArrayAgg

environ.setdefault(
    'DJANGO_SETTINGS_MODULE',
    'config.settings'
)
from django import setup
setup()

from device.common import CLIENT

from django.test import TestCase

from device.models import Definition
from pprint import pformat

logging.basicConfig(level=logging.DEBUG)


class TestDevice(TestCase):
    def setUp(self) -> None:
        self.definitions = Definition.objects \
            .filter(
                device__func='SET',
                user__ws_status=True
            ) \
            .values('device_id', 'device__name') \
            .annotate(numbers=ArrayAgg('number'))

    def test_check(self) -> None:
        CLIENT.connect(host=CLIENT.host, port=1883)

    def test_set_ws_status(self) -> None:
        for definition in self.definitions:
            mask = reduce(int.__or__.__call__, (0b11 << (_ - 1) * 2 for _ in definition['numbers']))
            event = f"MX210/{definition['device__name']}/SET/DO/MASK"
            values = CLIENT.publish(event, mask)
            assert values.rc == 0
            logging.info(f"{event=} {mask=}")
