
from django.contrib.auth.models import AbstractUser
from dataclasses import dataclass

from django.core.validators import MinValueValidator
from django.db import models


__all__ = ["User"]

from django.db.models import QuerySet

from device.models import Definition
from tariff.models import TariffPlan


class User(AbstractUser):
    address = models.OneToOneField("address.Address", verbose_name="Адрес", null=True, on_delete=models.CASCADE)
    balance = models.DecimalField(
        verbose_name="Баланс", max_digits=15, decimal_places=2,
        default=0., validators=[MinValueValidator(0)]
    )
    ws_status = models.BooleanField(verbose_name="Статус подачи воды", default=False)
    tariff_plan = models.ForeignKey(
        "tariff.TariffPlan", verbose_name="Тариф", blank=True,
        on_delete=models.PROTECT, null=True, related_name="tariff_planes"
    )
    next_tariff_plan = models.ForeignKey(
        "tariff.TariffPlan", verbose_name="Следующий тариф", blank=True,
        on_delete=models.PROTECT, null=True, related_name="next_tariff_planes"
    )
    auto_payment = models.BooleanField(verbose_name="Автооплата", default=False)
    start_datetime_pp = models.DateTimeField(verbose_name="Дата&Время начала оплаченного периода", blank=True, null=True)
    end_datetime_pp = models.DateTimeField(verbose_name="Дата&Время конца оплаченного периода", blank=True, null=True)
    phone = models.CharField(verbose_name="Номер телефона", max_length=15, null=True, unique=True)
    is_new = models.BooleanField(verbose_name="Новый пользователь", default=True)
    tariffs = models.ManyToManyField("tariff.TariffPlan", verbose_name="Все тарифы")

    definitions: QuerySet[Definition]

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

    def __str__(self) -> str:
        return self.username or f"{self.last_name} {self.first_name}"


@dataclass
class RegistrationCacheModel:
    method: str
    user: User
    tariff_plan: TariffPlan