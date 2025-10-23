from random import randint

from phonenumber_field.serializerfields import PhoneNumberField
from rest_framework import serializers

from account.models import User
from address.serializers import AddressSerializeChange
from config.tools import GetPa, Pa
from tariff.serializers import TariffPlanSerializerWithoutPa


class TargetCodeChoices:
    DEFAULT_AUTHCODE = "authcode"
    DEFAULT_REGCODE = "regcode"
    CHOICES = (
        (DEFAULT_AUTHCODE, "Код авторизации"),
        (DEFAULT_REGCODE, "Код регистрации")
    )
    LABEL = "След. операция"


class MethodCodeChoices:
    METHOD = serializers.ChoiceField(
        default="sms",
        choices=(
            ('sms', 'код по смс'),
            ('email', 'код по email')
        ),
        label="Метод"
    )


class Authorization(serializers.Serializer):
    login = serializers.CharField(label="Логин")
    target = serializers.ChoiceField(
        default=TargetCodeChoices.DEFAULT_AUTHCODE,
        choices=TargetCodeChoices.CHOICES,
        label=TargetCodeChoices.LABEL,
    )
    method = MethodCodeChoices.METHOD


class AuthorizationOperator(Authorization):
    password = serializers.CharField(label="Пароль")
    target = None
    method = None


class RegistrationUser(serializers.Serializer):
    phone = PhoneNumberField(
        label="Телефон", region='RU',
        default=type("", (str,), {
            '__str__': lambda _: "+79" + \
                "".join(str(randint(0, 9)) for _ in range(9))
        })()
    )
    pa = Pa.pa
    target = serializers.ChoiceField(
        default=TargetCodeChoices.DEFAULT_REGCODE,
        choices=TargetCodeChoices.CHOICES,
        label=TargetCodeChoices.LABEL,
    )
    method = MethodCodeChoices.METHOD


class ToDoubleNext(serializers.Serializer):
    id = serializers.UUIDField(label="Id задачи")
    target = serializers.ChoiceField(
        default=TargetCodeChoices.DEFAULT_REGCODE,
        choices=TargetCodeChoices.CHOICES,
        label=TargetCodeChoices.LABEL,
    )
    method = MethodCodeChoices.METHOD
    pa = Pa.pa


class RegistrationUserResponse(serializers.Serializer):
    pa = serializers.CharField(label="Лицевой счет")
    new = serializers.BooleanField(label="Не активирован ранее")
    status = serializers.CharField(default="Успешно!", label="Статус")
    action = serializers.CharField(default="registration", label="Действие")
    id = serializers.UUIDField(label="Id операции")
    tariff_plan = TariffPlanSerializerWithoutPa(read_only=True, label="Тариф")
    method = serializers.CharField(label="Метод", default="payment")


class AuthorizationResponse(serializers.Serializer):
    refresh = serializers.CharField()
    access = serializers.CharField()


class NextDoneId(serializers.Serializer):
    id = serializers.UUIDField(label="Id")


class Logout(serializers.Serializer):
    refresh = serializers.CharField()


class UserSerializeBase(serializers.ModelSerializer, GetPa):
    pa = GetPa.pa
    address = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'phone', 'email', 'address',
            'balance', 'ws_status', 'start_datetime_pp', 'end_datetime_pp',
            'pa', 'is_new', 'tariff_plan', 'next_tariff_plan'
        ]
        read_only_fields = [
            'balance', 'ws_status', 'start_datetime_pp',
            'end_datetime_pp', 'pa', 'is_new'
        ]

    @staticmethod
    def get_address(model) -> str | None:
        return str(model.address) if getattr(model, 'address', False) else None


class UserSerializerGet(UserSerializeBase):
    tariff_plan = TariffPlanSerializerWithoutPa(read_only=True)
    next_tariff_plan = TariffPlanSerializerWithoutPa(read_only=True)


class UserSerializerPost(UserSerializeBase):
    address = AddressSerializeChange()

    class Meta(UserSerializeBase.Meta):
        fields = [
            'first_name', 'last_name', 'phone', 'email',
            'address', 'tariff_plan', 'next_tariff_plan',
            'auto_payment'
        ]

    def update(self, instance: User, validated_data: dict):
        address = validated_data.pop('address', {})
        instance.address.__dict__.update(address)
        instance.__dict__.update(validated_data)
        if address:
            instance.address.save()
        instance.save()
        return instance


class UserSerializerPatch(UserSerializerPost):
    pass


class DataSerializer(serializers.ModelSerializer, GetPa):
    pa = GetPa.pa

    class Meta:
        model = User
        fields = ('pa', 'ws_status', 'start_datetime_pp', 'end_datetime_pp', 'is_new')
        read_only_fields = ('pa', 'ws_status', 'start_datetime_pp', 'end_datetime_pp', 'is_new')


class RegistrationUserMeta(RegistrationUser):
    target = None
    method = None
    pa = None


class DoubleAuthenticationSerializer(ToDoubleNext):
    pa = None
    method = None
    target = None
    code = serializers.CharField(min_length=6, max_length=6, label="Код")


class DoubleRegistrationSerializer(DoubleAuthenticationSerializer):
    pass


# ------------------------------------

class FastAuthUserSerializer(serializers.Serializer):
    login = serializers.CharField()