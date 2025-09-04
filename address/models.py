from typing import Any

from django.contrib.postgres.indexes import BTreeIndex
from django.db import models


class Address(models.Model):
    pa = models.PositiveIntegerField(verbose_name="Лицевой счет", primary_key=True)
    street = models.CharField(verbose_name="Улица", max_length=64, blank=False)
    house = models.CharField(verbose_name="Дом", max_length=6, blank=True, null=True)
    building = models.CharField(verbose_name="Корпус", max_length=6, blank=True, null=True)
    apartment = models.CharField(verbose_name="Квартира", max_length=6, blank=True, null=True)
    fias = models.UUIDField(verbose_name="ФИАС", null=True)
    join = models.TextField(verbose_name="Адрес", max_length=255)

    class Meta:
        indexes = [BTreeIndex(fields=['join'])]

    def __str__(self) -> str:
        return ', '.join(filter(bool, (
            f'ул. {self.street}',
            f'д. {self.house}' if self.house else None,
            f'корп. {self.building}' if self.building else None,
            f'кв. {self.apartment}' if self.apartment else None
        )))

    def __getattribute__(self, item: str) -> Any:
        if item == 'pa':
            return f'{sum(map(ord, str(self))):0>12}'
        elif item in (
            'house',
            'building',
            'apartment',
        ):
            return (super().__getattribute__(item) or '').lower()
        elif item == 'street':
            return super().__getattribute__('street').title()
        return super().__getattribute__(item)
