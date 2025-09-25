
from rest_framework import serializers

from account.models import User
from address.models import Address
from address.serializers import AddressSerializeChange, AddressSerializeList
from config.tools import GetPa, Pa
from tariff.serializers import TariffPlanSerializerWithoutPa
from phonenumber_field.serializerfields import PhoneNumberField


class Authorization(serializers.Serializer):
    login = serializers.CharField(label="Логин")
    target = serializers.CharField(default="code", label="След. операция")
    method = serializers.ChoiceField(default="sms", choices=(
        ('sms', 'код по смс'),
        ('email', 'код по email')
    ), label="Метод")
    
    class Meta:
        fields = ["__all__"]


class AuthorizationOperator(Authorization):
    target = None
    method = None


class RegistrationUser(serializers.Serializer):
    phone = PhoneNumberField(label="Телефон", region='RU')
    apartment = serializers.CharField(label="Квартира")
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
        fields = ('pa', 'ws_status', 'start_datetime_pp', 'end_datetime_pp')
        read_only_fields = ('ws_status', 'start_datetime_pp', 'end_datetime_pp')

    @staticmethod
    def get_pa(model: dict) -> str:
        return f'{model.get('pa', ''):0>12}'


class TargetResposneSerializer(serializers.Serializer):
    id = serializers.UUIDField(label="Id задачи")
    target = serializers.CharField(default="code", label="Действие")
    method = serializers.ChoiceField(default="sms", choices=(
        ('sms', 'код по смс'),
        ('email', 'код по email')
    ), label="Метод")


class DoubleAuthenticationSerializer(TargetResposneSerializer):
    target = None
    method = None
    code = serializers.CharField(min_length=6, max_length=6, label="Код")


# ------------------------------------

class FastAuthUserSerializer(serializers.Serializer):
    login = serializers.CharField()