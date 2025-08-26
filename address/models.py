from typing import Any, Self

from django.db import models
from random import randint


def _random_pa() -> int:
    rand_list = {randint(11111, 2147483646) for _ in range(10)}
    re_values = Address.objects.filter(pa__in=rand_list).only('pa')
    rand_list.difference_update(re_values)
    return next(iter(rand_list), None) or _random_pa()


class Address(models.Model):
    pa = models.PositiveIntegerField(verbose_name="Лицевой счет", primary_key=True, default=_random_pa)
    street = models.CharField(verbose_name="Улица", blank=False)
    house = models.CharField(verbose_name="Дом", blank=True, null=True)
    building = models.CharField(verbose_name="Корпус", blank=True, null=True)
    apartment = models.CharField(verbose_name="Квартира", blank=True, null=True)
    fias = models.UUIDField(verbose_name="ФИАС", null=True)

    def __str__(self) -> str:
        return ', '.join(filter(bool, (
            f'ул. {self.street}',
            f'д. {self.house}' if self.house else None,
            f'корп. {self.building}' if self.building else None,
            f'кв. {self.apartment}' if self.apartment else None
        )))

    def __getattribute__(self, item: str) -> Any:
        field = super().__getattribute__(item)
        if item == 'pa':
            return f'{field:0>12}'
        return field


