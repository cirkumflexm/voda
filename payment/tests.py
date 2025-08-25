import logging
from time import sleep

from django.test import TestCase
from service import *

from pprint import pprint


logger = logging.getLogger(__name__)


class Payment(TestCase):
    def test_create_payment(self) -> None:
        try:
            payment = create_payment(
                num=324,
                price=1200.00,
                currency="RUB",
                tariff_name="Тариф номер 1",
                full_name="ВодоПроект",
                user_phone="",
                user_email="nopelllek@gmail.com",
                user_id=1,
                tariff_id=1,
                return_url="https://www.example.com/return_url"
            )
            pprint(payment)

            for _ in range(120):
                status = find_payment(payment_id=payment["response_data"]["id"])
                print(status)
                if status["status"] == "waiting_for_capture":
                    print(status)
                    print(capture_payment(payment_id=payment["response_data"]["id"]))
                    break
                sleep(5)
        except ApiError as ex:
            print(ex.content["code"])