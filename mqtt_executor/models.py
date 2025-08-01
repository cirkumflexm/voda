
from django.db import models


class Device(models.Model):
    factory_number = models.BigIntegerField(
        verbose_name="Заводской номер"
    )
    dev_name = models.CharField(
        max_length=100,
        verbose_name="Название устройства"
    )
    name = models.CharField(
        max_length=100,
        verbose_name="Название"
    )
    path = models.CharField(max_length=255, verbose_name="Путь MQTT")
    offset = models.SmallIntegerField(verbose_name="Сдвиг")


class Encoard(models.Model):
    device = models.ForeignKey(
        "Device",
        on_delete=models.CASCADE
    )
    number = models.IntegerField(
        verbose_name="Дискретный вход / Дискретный выход",
        default=0
    )
    user = models.ForeignKey(
        "account.User",
        on_delete=models.CASCADE,
        related_name="encoarded",
        default=0
    )

