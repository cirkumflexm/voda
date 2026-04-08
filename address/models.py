
from django.contrib.postgres.indexes import GistIndex
from django.db import models


class Address(models.Model):
    seed = models.PositiveIntegerField(verbose_name="Сид лицевого счета", unique=True, editable=False)
    pa = models.CharField(max_length=12, verbose_name="ID Лицевого счета", primary_key=True, editable=False)
    street = models.CharField(verbose_name="Улица", max_length=64, blank=False, editable=False)
    house = models.CharField(verbose_name="Дом", max_length=64, blank=True, editable=False)
    apartment = models.CharField(verbose_name="Квартира", max_length=64, blank=True, null=True, editable=False)
    apartment_type = models.CharField(verbose_name="Тип помещения", max_length=6, blank=True, null=True, editable=False)
    apartment_sort = models.PositiveIntegerField(verbose_name="Номер квартиры в числовом формате", blank=True, null=True, editable=False)
    fias = models.UUIDField(verbose_name="ФИАС", unique=True, editable=False)
    line = models.TextField(verbose_name="Адрес", max_length=255, editable=False)
    city = models.CharField(verbose_name="Город", max_length=255, editable=False)
    parent = models.ForeignKey("address.Address", on_delete=models.SET_NULL, null=True, editable=False)

    class Meta:
        verbose_name = "Адрес (FIAS)"
        verbose_name_plural = "Адреса (FIAS)"

        indexes = [
            GistIndex(
                fields=['line'], 
                name='line_trgm_idx', 
                opclasses=['gist_trgm_ops']
            )
        ]

    def __str__(self) -> str:
        return self.line


class IncompleteAddressManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(apartment__isnull=True)


class IncompleteAddress(Address):
    objects = IncompleteAddressManager()

    class Meta:
        verbose_name = "Адрес (дома/строения)"
        verbose_name_plural = "Адреса (дома/строения)"
        proxy = True


