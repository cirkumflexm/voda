
from account.models import User

from django.db import models


class Payment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    quantity = models.DecimalField(verbose_name="Сумма", max_digits=15, decimal_places=2)
    datetime = models.DateTimeField(verbose_name="Дата&Время", auto_now=True)

    class Meta:
        verbose_name = "Оплата"
        verbose_name_plural = "Оплаты"