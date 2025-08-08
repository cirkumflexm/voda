
from rest_framework import serializers

from account.models import User
from tariff.serializers import TariffPlanSerializer


class Authorization(serializers.ModelSerializer):
    login = serializers.CharField()
    class Meta:
        model = User
        fields = ["login", "password"]


class Registration(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["phone", "email", "first_name", "last_name"]


class AuthorizationResponseOk(serializers.Serializer):
    refresh = serializers.CharField()
    access = serializers.CharField()


class RegistrationResponseOk(serializers.Serializer):
    status = serializers.CharField(default="Ok")


class Logout(serializers.Serializer):
    refresh = serializers.CharField()


class UserSerializerGet(serializers.ModelSerializer):
    tariff_plan = TariffPlanSerializer()

    class Meta:
       model = User

       fields = [
           'id', 'first_name', 'last_name', 'phone', 'email', 'username', 'address', 'apartment', 'fias',
           'balance', 'ws_status', 'tariff_plan', 'start_datetime_pp', 'end_datetime_pp', 'personal_account'
       ]
       read_only_fields = ['username', 'balance', 'ws_status', 'start_datetime_pp', 'end_datetime_pp', 'personal_account']


class UserSerializer(serializers.ModelSerializer):
    class Meta:
       model = User

       fields = [
           'id', 'first_name', 'last_name', 'phone', 'email', 'address', 'apartment', 'fias',
           'balance', 'ws_status', 'tariff_plan', 'start_datetime_pp', 'end_datetime_pp', 'personal_account'
       ]
       read_only_fields = ['username', 'personal_account', 'balance', 'ws_status', 'start_datetime_pp', 'end_datetime_pp']


class DataSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['personal_account', 'ws_status', 'start_datetime_pp', 'end_datetime_pp']
        read_only_fields = ['personal_account', 'ws_status', 'start_datetime_pp', 'end_datetime_pp']