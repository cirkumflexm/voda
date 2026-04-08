
from random import randint
from unittest import TestCase
from django.db.models import QuerySet
from account.models import User
from address.tests import TestAddress
from tariff.tests import TestTariff


class TestUser(TestCase):
    def create(self):
        tariff = TestTariff('test_tariff').create()
        user = User(
            address=TestAddress('test_address').create(),
            tariff_plan=tariff,
            next_tariff_plan=tariff,
            phone='+79' + ''.join((str(randint(0, 9)) for _ in range(9))),
            is_new=False
        )
        user.tariffs.add(tariff)
        user.save(using='test')
        print(user)
        return user

    def test_create(self):
        self.create()
