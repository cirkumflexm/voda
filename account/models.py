
from django.contrib.auth.models import AbstractUser
from django.db import models


__all__ = ["User"]

from django.db.models import QuerySet

from device.models import Definition
from tariff.models import TariffPlan


class User(AbstractUser):
    personal_account = models.CharField(verbose_name="Лс счет", null=True, unique=True, db_index=True)
    address = models.CharField(verbose_name="Адрес", max_length=255, null=True)
    apartment = models.CharField(verbose_name="Квартира", max_length=11, null=True)
    fias = models.CharField(verbose_name="ФИАС", max_length=47, default="")
    balance = models.DecimalField(verbose_name="Баланс", max_digits=15, decimal_places=2, default=0.)
    ws_status = models.BooleanField(verbose_name="Статус подачи воды", default=False)
    tariff_plan = models.ForeignKey(
        "tariff.TariffPlan", verbose_name="Тариф", blank=True,
        on_delete=models.PROTECT, null=True, related_name="tariff_planes"
    )
    next_tariff_plan = models.ForeignKey(
        "tariff.TariffPlan", verbose_name="Следующий тариф", blank=True,
        on_delete=models.SET_NULL, null=True, related_name="next_tariff_planes"
    )
    start_datetime_pp = models.DateTimeField(verbose_name="Дата&Время начала оплаченного периода", blank=True, null=True)
    end_datetime_pp = models.DateTimeField(verbose_name="Дата&Время конца оплаченного периода", blank=True, null=True)
    phone = models.CharField(verbose_name="Номер телефона", max_length=15, null=True, unique=True)
    is_new = models.BooleanField(verbose_name="Новый пользователь", default=True)

    definitions: QuerySet[Definition]
    tariff_choices: QuerySet[TariffPlan]

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

    def __str__(self) -> str:
        return self.username
