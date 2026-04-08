
from django.db.models import QuerySet
from unittest import TestCase

from tariff.models import TariffPlan


class TestTariff(TestCase):
    @staticmethod
    def create():
        tariff = QuerySet(TariffPlan).using('test').get_or_create(
            uuid='e7d7fbf2-e989-47c5-a7d8-b080b200fd77',
            name='Тариф',
            price=100.,
            unit_measurement='day'
        )
        print(tariff)
        return tariff

    def test_create(self):
        return self.create()
