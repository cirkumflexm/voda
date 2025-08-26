
from rest_framework import serializers

from account.models import User
from address.serializers import AddressSerializeChange
from tariff.serializers import TariffPlanSerializer


class Authorization(serializers.Serializer):
    login = serializers.CharField()
    password = serializers.CharField()
    target = serializers.CharField(default="code", label="Действие")
    method = serializers.ChoiceField(default="sms", choices=(
        ('sms', 'код по смс'),
        ('email', 'код по email')
    ), label="Метод")
    
    class Meta:
        fields = ["__all__"]


class AuthorizationOperator(Authorization):
    target = None
    method = None


class Registration(serializers.Serializer):
    phone = serializers.CharField()
    email = serializers.CharField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    class Meta:
        fields = ["__all__"]


class AuthorizationResponseOk(serializers.Serializer):
    refresh = serializers.CharField()
    access = serializers.CharField()


class RegistrationResponseOk(serializers.Serializer):
    status = serializers.CharField(default="Ok")


class Logout(serializers.Serializer):
    refresh = serializers.CharField()


class UserSerializeBase(serializers.ModelSerializer):
    pa = serializers.SerializerMethodField()
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
    def get_pa(model) -> str | None:
        return f'{model.address.pa:0>12}' if getattr(model.address, 'pa', False) else None

    @staticmethod
    def get_address(model) -> str | None:
        return str(model.address) if getattr(model, 'address', False) else None


class UserSerializerGet(UserSerializeBase):
    tariff_plan = TariffPlanSerializer(read_only=True)
    next_tariff_plan = TariffPlanSerializer(read_only=True)


class UserSerializerPost(UserSerializeBase):
    address = AddressSerializeChange()

    class Meta(UserSerializeBase.Meta):
        fields = [
            'first_name', 'last_name', 'phone', 'email',
            'address', 'tariff_plan', 'next_tariff_plan'
        ]

    def update(self, instance: User, validated_data: dict):
        print(validated_data)
        address = validated_data.pop('address', {})
        instance.address.__dict__.update(address)
        instance.__dict__.update(validated_data)
        if address:
            instance.address.save()
        instance.save()
        return instance


class UserSerializerPatch(UserSerializerPost):
    pass


class DataSerializer(serializers.ModelSerializer):
    pa = serializers.SerializerMethodField()

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
    code = serializers.CharField(min_length=6, max_length=6)


# ------------------------------------

class FastAuthUserSerializer(serializers.Serializer):
    login = serializers.CharField()