from typing import TYPE_CHECKING, Iterable

from django.contrib.auth.models import AbstractUser, BaseUserManager
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
    definition = models.ForeignKey('device.Definition', on_delete=models.CASCADE, null=True, verbose_name='Подключенный порт')
    fio = models.CharField(max_length=128, verbose_name='ФИО', null=True)
    last_name = None
    first_name = None

    @property
    def group(self) -> str:
        group = self.groups.get()
        return group.name

    if group.fget:
        group.fget.short_description = 'Группа'

    if TYPE_CHECKING:
        objects: models.Manager['User']

    class Meta:
        verbose_name = "Пользователя"
        verbose_name_plural = "Пользователи"

    def __str__(self) -> str:
        return self.username


class WrapperUserManager(models.Manager):
    normalize_email = BaseUserManager.normalize_email

    def __init__(self, is_staff: bool = True) -> None:
        super().__init__()
        self.is_staff = is_staff

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.filter(
                is_superuser=False, is_staff=self.is_staff)


class Client(User):
    objects = WrapperUserManager(is_staff=False)

    class Meta:
        proxy = True
        verbose_name = 'Клиента'
        verbose_name_plural = 'Клиенты'


class Operator(User):
    objects = WrapperUserManager(is_staff=True)

    class Meta:
        proxy = True
        verbose_name = 'Оператора'
        verbose_name_plural = 'Операторы'

    def save(
            self,
            force_insert: bool = False,
            force_update: bool = False,
            using: str | None = None,
            update_fields: Iterable[str] | None = None
    ) -> None:
        super().save(
            force_insert,
            force_update,
            using,
            update_fields
        )
        self.groups.add(2)
