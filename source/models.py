from decimal import Decimal

from django.db.models import QuerySet

from django.db import models

__all__ = [
    "QuerySet",
    "TariffPlan",
    "ServiceArchive"
]


class TariffPlan(models.Model):
    name = models.CharField(max_length=255, verbose_name="Название")
    price = models.DecimalField(verbose_name="Поле Цена в рублях", max_digits=15, decimal_places=2)
    archive = models.BooleanField(verbose_name="Признак архивности", default=False)
    unit_measurement = models.CharField(
        verbose_name="Единица измерения", max_length=9,
        choices={
            "day": "день",
            "month": "месяц",
            "quarter": "квартал",
            "halfyear": "полгода",
            "year": "год"
        }
    )

    class Meta:
        verbose_name = "Тариф"
        verbose_name_plural = "Тарифы"

    def save(self, *args, **kw):
        if self.price < Decimal('0.0'):
            raise ValueError("Цена не может быть отрицательной.")
        if self.unit_measurement not in (
            "day",
            "month",
            "quarter",
            "halfyear",
            "year"
        ):
            raise ValueError("Неправильно указан временной промежуток. " 
                             "Требуется: (\"day\", \"month\", \"quarter\", \"halfyear\", \"year\").")
        super().save(*args, **kw)

    def __str__(self) -> str:
        __values = ', '.join(f"{k}={getattr(self, k)}" for k in ('name', 'price'))
        return "%s(%s)" % (self.__class__.__name__, __values)


class ServiceArchive(models.Model):
    user = models.ForeignKey('account.User', on_delete=models.CASCADE, related_name="services_archive")
    start_datetime_pp = models.DateTimeField(verbose_name="Дата&Время начала оплаченного периода")
    end_datetime_pp = models.DateTimeField(verbose_name="Дата&Время конца оплаченного периода")
    tariff_plan = models.ForeignKey("TariffPlan", verbose_name="Тариф", on_delete=models.PROTECT)

    class Meta:
        verbose_name = "Архив услуг"
        verbose_name_plural = "Архивы услуг"

