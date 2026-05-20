from collections import defaultdict
from datetime import timedelta
from functools import lru_cache
from secrets import token_hex
from uuid import uuid4
from asgiref.sync import sync_to_async
from hashlib import sha256
from typing import TYPE_CHECKING, Any, Callable, Iterable, Self, Optional
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models, transaction
from django.utils import timezone
from django.utils.text import slugify
from django.db.models.base import ModelBase
from django.db.models.functions import Concat
from transliterate import translit
from string import ascii_letters, ascii_uppercase
from django.utils.crypto import get_random_string

from address.models import Address



CHARS = "!@#$%^*()" + ascii_uppercase + ascii_letters

@lru_cache(maxsize=1)
def get_pdf_template() -> str:
    with open('device/templates/pdf.html', 'r') as f:
        return f.read()


class DeviceMeta(ModelBase):
    def __new__(
            cls, name: str,
            bases: tuple[type, ...],
            attrs: dict[str, Any],
            **kwargs: Any
    ) -> ModelBase:
        for num in range(1, 9):
            field = property(*cls.port(num))
            field.fget.short_description = f'Порт {num}'  # pyright: ignore[reportOptionalMemberAccess]
            attrs[f'port_{num}'] = field
        return super().__new__(cls, name, bases, attrs, **kwargs)

    @staticmethod
    def port(num: int) -> tuple[Callable, Callable]:

        def __wrapper_fget(self: "Device"):
            if num not in self._local_definitions:
                for definition in Definition.objects \
                        .select_related('address') \
                        .only('port', 'address__apartment', 'address__apartment_type') \
                        .filter(device=self):
                    self._local_definitions[definition.port] = definition
            definition = self._local_definitions[num]
            return definition.address

        def __wrapper_fset(self: "Device", address: "DefinitionAddress") -> None:
            definition = self._local_definitions[num]
            definition.address = address

        return __wrapper_fget, __wrapper_fset


class DeviceManager(models.Manager):
    def get_queryset(self) -> models.QuerySet["Device"]:
        return super().get_queryset()


class Device(models.Model, metaclass=DeviceMeta):
    uuid = models.CharField(
        default=uuid4,
        editable=False,
        blank=True
    )
    number = models.CharField(
        max_length=16,
        verbose_name="Заводской номер",
        unique=True
    )
    username = models.CharField(
        max_length=32,
        verbose_name='Логин устройства',
        unique=True,
        db_index=True,
        editable=False
    )
    password = models.CharField(
        max_length=256,
        verbose_name='Хеш пароль',
        editable=False,
        null=True
    )
    name = models.CharField(
        max_length=100,
        verbose_name="Уникальное имя",
        unique=True,
        editable=False
    )
    uniqueness = models.PositiveIntegerField(
        verbose_name="Число для уникальности имени",
        editable=False,
        null=False
    )
    delete_at = models.DateTimeField(
        verbose_name="Автоудаление через",
        null=True,
        editable=False
    )
    created_at = models.DateTimeField(
        auto_now=True,
        editable=False
    )
    address = models.ForeignKey(
        "address.IncompleteAddress",
        on_delete=models.CASCADE,
        verbose_name="Адрес устройства",
    )
    isnot_online = models.BooleanField(editable=False, null=True)

    if TYPE_CHECKING:
        objects: models.Manager['Device']
        definitions: models.Manager["Definition"]

    @property
    def status(self) -> str:
        return {1: 'не в сети', 0: 'в сети', None: 'отсутвует'}[self.isnot_online]
    status.fget.short_description = 'Состояние'  # pyright: ignore[reportOptionalMemberAccess]

    @property
    def delete_via(self) -> str:
        if self.delete_at is not None:
            via = self.delete_at - timezone.now()
            return f'через {via.total_seconds() // 3600:.0f} ч.'
        else:
            return '-'
    delete_via.fget.short_description = 'Автоудаление'  # pyright: ignore[reportOptionalMemberAccess]

    class Meta:
        verbose_name = "Устройство (MX210)"
        verbose_name_plural = "Устройства (MX210)"

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._local_definitions = defaultdict(lambda: Definition(device=self))

    def __str__(self) -> str:
        return self.name

    def save(
            self, *,
            force_insert: bool | tuple[ModelBase, ...] = False,
            force_update: bool = False,
            using: str | None = None,
            update_fields: Iterable[str] | None = None
    ) -> None:
        with transaction.atomic():
            if self.pk is None:
                street = self.address.street
                house = self.address.house
                first_device = Device.objects \
                        .only('uniqueness') \
                        .filter(address_id=self.address.pa) \
                        .order_by('-uniqueness') \
                        .first()
                if first_device:
                    self.uniqueness = first_device.uniqueness + 1
                else:
                    self.uniqueness = 1
                name = f'{street} {house} {self.uniqueness}'
                name = translit(name, language_code='ru', reversed=True)
                self.name = slugify(name)
                self.username = token_hex(6)
                self.delete_at = timezone.now() + timedelta(hours=72)
            super().save()
            if self._local_definitions:
                definitions = []
                for key, value in self._local_definitions.items():
                    value.device = self
                    value.port = key
                    definitions.append(value)
                Definition.objects.filter(device=self).delete()
                Definition.objects.bulk_create(definitions)

    @classmethod
    @sync_to_async
    def hash_check(cls, username: str, password: str) -> Optional[Self]:
        hash_string = sha256(password.encode()).hexdigest()
        return cls.objects.filter(username=username, password=hash_string).first()

    @sync_to_async()
    def xml(self) -> str:
        password = get_random_string(12, CHARS)
        self.password = sha256(password.encode()).hexdigest()
        super().save(update_fields=('password',))
        context = {
            'number': self.number,
            'address': self.address.line,
            'password': password,
            'username': self.username,
            'name': self.name,
            'port_1': str(getattr(self, 'port_1') or '-'),
            'port_2': str(getattr(self, 'port_2') or '-'),
            'port_3': str(getattr(self, 'port_3') or '-'),
            'port_4': str(getattr(self, 'port_4') or '-'),
            'port_5': str(getattr(self, 'port_5') or '-'),
            'port_6': str(getattr(self, 'port_6') or '-'),
            'port_7': str(getattr(self, 'port_7') or '-'),
            'port_8': str(getattr(self, 'port_8') or '-'),
        }
        return get_pdf_template().format(**context)


class Definition(models.Model):
    device = models.ForeignKey(
        "Device",
        on_delete=models.CASCADE,
        related_name="definitions",
    )
    port = models.IntegerField(
        verbose_name="Дискретный вход / Дискретный выход",
        null=True,
        validators=[
            MaxValueValidator(8),
            MinValueValidator(1)
        ],
        editable=False
    )
    address = models.OneToOneField(
        "device.DefinitionAddress",
        verbose_name="Квартира/Помещение",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name='definitions'
    )

    class Meta:
        verbose_name = "Порт"
        verbose_name_plural = "Порты"

        constraints = [
            models.UniqueConstraint(
                fields=['device', 'port'],
                name='unique_device_port'
            ),
            models.UniqueConstraint(
                fields=['address'],
                name='unique_address'
            )
        ]


class DefinitionAddressManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset() \
            .only('parent', 'pa') \
            .annotate(apartment_value=Concat('apartment_type', models.Value(' '), 'apartment')) \
            .order_by('apartment_sort')


class DefinitionAddress(Address):
    objects = DefinitionAddressManager()
    apartment_value: str

    def __str__(self) -> str:
        if hasattr(self, "apartment_value"):
            return self.apartment_value
        else:
            return f"{self.apartment_type} {self.apartment}"

    class Meta:
        proxy = True


class LogDevice(models.Model):
    action = models.CharField(max_length=20, verbose_name='Действие')
    payload = models.JSONField(verbose_name='JSON')
    created_at = models.DateTimeField(null=False, auto_now=True, verbose_name='Создан')

    class Meta:
        verbose_name = 'Журнал'
        verbose_name_plural = 'Журнал'

    @classmethod
    def easy_create(cls, action: str, payload: dict) -> None:
        cls.objects.create(action=action, payload=payload)

    @classmethod
    @sync_to_async()
    def aeasy_create(cls, action: str, payload: dict) -> None:
        cls.easy_create(action, payload)

