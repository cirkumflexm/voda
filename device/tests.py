import logging

from django import setup

setup()

from celery.exceptions import CeleryError
from unittest import TestCase
from device.tasks import set_ws_s_task


logging.basicConfig(level=logging.DEBUG)


class TestDevice(TestCase):

    def test_set_ws_status(self) -> None:
        try:
            set_ws_s_task()
        except CeleryError:
            pass