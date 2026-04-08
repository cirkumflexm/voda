import logging

from django import setup
from lxml import html
from fast_pdf_gen import generate_pdf, compile_handlebars_template

from device.models import Device

setup()

# from celery.exceptions import CeleryError
from unittest import TestCase
# from device.tasks import set_ws_s_task
#

logging.basicConfig(level=logging.DEBUG)


class TestDevice(TestCase):

    def test_set_ws_status(self) -> None:
        try:
            set_ws_s_task()
        except CeleryError:
            pass

    def test_pdf(self) -> None:
        devices = Device.objects.all()
        xml = ''.join(_.xml() for _ in devices)
        generate_pdf(
            "my_unique_key", 
            xml, 
            'test.pdf',
            pdf_options={
                'format': 'A4',
                'margin': {
                   'top': '10mm',
                   'bottom': '10mm',
                }
            }
        )
