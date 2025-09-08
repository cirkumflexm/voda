from django.db import models, IntegrityError

from account.models import User

from string import ascii_letters, digits
from random import choice, randint


class Promo(models.Model):
    uuid = models.UUIDField(auto_created=True, verbose_name="UUID", primary_key=True)
    label = models.CharField(max_length=32, verbose_name="Промо", unique=True)
    tariff_plan = models.ForeignKey(
        "tariff.TariffPlan", on_delete=models.PROTECT,
        verbose_name="Тариф"
    )
    for_user = models.OneToOneField(
        "account.User", on_delete=models.PROTECT,
        verbose_name="Пользователь", null=True
    )

    class Meta:
        verbose_name = "Промокод"
        verbose_name_plural = "Промокоды"

    @classmethod
    def create_random_promo(cls, for_user: User, count: int = 1) -> None:
        try:
            cls.objects.create(
                label="".join(choice(ascii_letters + digits) for _ in range(randint(7, 10))),
                count=count,
                for_user=for_user
            )
        except IntegrityError:
            cls.create_random_promo(for_user, count)


class PromoActivation(models.Model):
    label = Promo.label
    user = Promo.for_user
    datetime = models.DateTimeField(auto_now=True, verbose_name="Дата&Время")

    class Meta:
        verbose_name = "Промо-активация"
        verbose_name_plural = "Промо-активации"
