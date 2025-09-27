
__all__ = [
    "QuerySet",
    "TariffPlan",
    "ServiceArchive"
]

from decimal import Decimal
from typing import Self
from uuid import uuid4

from django.core.validators import MinValueValidator
from django.db.models import QuerySet
from django.db import models


class TariffPlan(models.Model):
    uuid = models.UUIDField(primary_key=False, verbose_name="UUID тарифа", auto_created=True)
    name = models.CharField(max_length=255, verbose_name="Название")
    price = models.DecimalField(
        verbose_name="Поле Цена в рублях", max_digits=15, decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    archive = models.BooleanField(verbose_name="Признак архивности", default=False)
    unit_measurement = models.CharField(
        verbose_name="Единица измерения",
        max_length=9,
        choices=(
            ("day", "день"),
            ("month", "месяц"),
            ("two month", "два месяца"),
            ("quarter", "квартал"),
            ("halfyear", "полгода"),
            ("year", "год"),
            ("constant", "навсегда")
        )
    )
    is_test = models.BooleanField(verbose_name="Тестовый тариф", default=False)

    class Meta:
        verbose_name = "Тариф"
        verbose_name_plural = "Тарифы"

    def save(self, *args, **kw):
        self.uuid = uuid4()
        super().save(*args, **kw)

    def __str__(self) -> str:
        __values = ', '.join(f"{k}={getattr(self, k)}" for k in ('name', 'price'))
        return "%s(%s)" % (self.__class__.__name__, __values)

    @classmethod
    def create_test_tariff_plan(cls, user) -> Self:
        test_tariff_plan = cls(
            name="Тестовый тариф",
            price=1.00,
            unit_measurement="day",
            is_test=True
        )
        test_tariff_plan.uuid = uuid4()
        user.tariff_plan = test_tariff_plan
        return test_tariff_plan


class ServiceArchive(models.Model):
    user = models.ForeignKey('account.User', on_delete=models.CASCADE, related_name="services_archive")
    start_datetime_pp = models.DateTimeField(verbose_name="Дата&Время начала оплаченного периода")
    end_datetime_pp = models.DateTimeField(verbose_name="Дата&Время конца оплаченного периода")
    tariff_plan = models.ForeignKey("TariffPlan", verbose_name="Тариф", on_delete=models.PROTECT)

    class Meta:
        verbose_name = "Архив услуг"
        verbose_name_plural = "Архивы услуг"

