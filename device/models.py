
from django.db import models


class Device(models.Model):
    factory_number = models.BigIntegerField(
        verbose_name="Заводской номер"
    )
    # dev_name = models.CharField(
    #     max_length=100,
    #     verbose_name="Название устройства",
    #     null=True
    # )
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

