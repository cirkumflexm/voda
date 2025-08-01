
from decimal import Decimal

from django.contrib.auth.models import AbstractUser
from django.db import models


__all__ = ["User"]

from django.db.models import QuerySet

from device.models import Encoard


class User(AbstractUser):
    personal_account = models.CharField(verbose_name="Лс счет", null=True, unique=True)
    address = models.CharField(verbose_name="Адрес", max_length=255, default="")
    apartment = models.CharField(verbose_name="Квартира", max_length=11, null=True)
    fias = models.CharField(verbose_name="ФИАС", max_length=47, default="")
    balance = models.DecimalField(verbose_name="Баланс", max_digits=15, decimal_places=2, default=0.)
    ws_status = models.BooleanField(verbose_name="Статус подачи воды", default=False)
    tariff_plan = models.ForeignKey("source.TariffPlan", verbose_name="Тариф", on_delete=models.PROTECT, null=True)
    start_datetime_pp = models.DateTimeField(verbose_name="Дата&Время начала оплаченного периода", null=True)
    end_datetime_pp = models.DateTimeField(verbose_name="Дата&Время конца оплаченного периода", null=True)
    phone = models.CharField(verbose_name="Номер телефона", max_length=15, null=True, unique=True)

    encoarded: Encoard

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

    def __str__(self) -> str:
        return self.username
