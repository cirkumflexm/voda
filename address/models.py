
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
        return self.get_join()

    def get_pa(self) -> str:
        return self.pa or f'{sum(map(ord, str(self))):0>12}'
        
    def get_join(self) -> str:
        return self.join or ', '.join(filter(bool, (
            f'ул. {self.street}',
            f'д. {self.house}' if self.house else None,
            f'корп. {self.building}' if self.building else None,
            f'кв. {self.apartment}' if self.apartment else None
        )))

    def save(self, *args, **kw) -> None:
        self.pa = self.get_pa()
        self.join = self.get_join()
        super().save(*args, **kw)