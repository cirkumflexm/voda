from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models


class Device(models.Model):
    factory_number = models.BigIntegerField(
        verbose_name="Заводской номер"
    )
    name = models.CharField(
        max_length=100,
        verbose_name="Уникальное имя устройства в сети mqtt",
        unique=True
    )
    func = models.CharField(
        max_length=6,
        verbose_name="Функция",
        default="",
        choices={
            "SET": "SET",
            "GET": "GET"
        }
    )


class Definition(models.Model):
    device = models.ForeignKey(
        "Device",
        on_delete=models.CASCADE,
        related_name="definitions",
    )
    number = models.IntegerField(
        verbose_name="Дискретный вход / Дискретный выход",
        default=0,
        validators=[
            MaxValueValidator(6),
            MinValueValidator(1)
        ]
    )
    address = models.OneToOneField(
        "address.Address",
        verbose_name="Адрес",
        null=True,
        on_delete=models.PROTECT
    )