
from rest_framework import serializers

from account.models import User
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


class UserSerializerGet(serializers.ModelSerializer):
    tariff_plan = TariffPlanSerializer(read_only=True)
    next_tariff_plan = TariffPlanSerializer(read_only=True)

    class Meta:
       model = User

       fields = [
           'id', 'first_name', 'last_name', 'phone', 'email', 'username', 'address', 'apartment', 'fias',
           'balance', 'ws_status', 'tariff_plan', 'next_tariff_plan',
           'start_datetime_pp', 'end_datetime_pp', 'personal_account', 'is_new'
       ]
       read_only_fields = [
           'username', 'balance', 'ws_status',
           'start_datetime_pp', 'end_datetime_pp',
           'personal_account', 'is_new'
       ]


class UserSerializerPost(serializers.ModelSerializer):
    class Meta:
       model = User

       fields = [
           'id', 'first_name', 'last_name', 'phone', 'email', 'address', 'apartment', 'fias',
           'balance', 'ws_status', 'tariff_plan',
           'start_datetime_pp', 'end_datetime_pp', 'personal_account', 'is_new'
       ]
       read_only_fields = [
           'username', 'personal_account', 'balance',
           'ws_status', 'start_datetime_pp', 'end_datetime_pp', 'is_new'
       ]

class UserSerializerPatch(serializers.ModelSerializer):
    class Meta:
       model = User

       fields = [
           'id', 'first_name', 'last_name', 'phone', 'email', 'address', 'apartment', 'fias',
           'balance', 'ws_status', 'tariff_plan', 'next_tariff_plan',
           'start_datetime_pp', 'end_datetime_pp', 'personal_account', 'is_new'
       ]
       read_only_fields = [
           'username', 'personal_account', 'balance',
           'ws_status', 'start_datetime_pp', 'end_datetime_pp', 'is_new'
       ]


class DataSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['personal_account', 'ws_status', 'start_datetime_pp', 'end_datetime_pp']
        read_only_fields = ['personal_account', 'ws_status', 'start_datetime_pp', 'end_datetime_pp']


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