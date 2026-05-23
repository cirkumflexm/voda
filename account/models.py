from typing import TYPE_CHECKING

from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator
from django.db import models

__all__ = ["User"]


class User(AbstractUser):
    address = models.ForeignKey(
        "address.Address", verbose_name="Адрес",
        null=True, on_delete=models.PROTECT
    )
    balance = models.DecimalField(
        verbose_name="Баланс", max_digits=15, decimal_places=2,
        default=0, validators=[MinValueValidator(0)]
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
    payment_method = models.CharField(max_length=36, verbose_name="ID автоплатежа", null=True, blank=True)
    is_verified = models.BooleanField(verbose_name="Пользователь подтвержден", default=False, blank=False)
    definition = models.ForeignKey('device.Definition', on_delete=models.CASCADE, null=True)
    last_name = None
    first_name = None

    if TYPE_CHECKING:
        objects: models.Manager['User']

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

    def __str__(self) -> str:
        return self.username
