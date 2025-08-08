
from rest_framework import serializers

from account.models import User
from .models import *


class DeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Device
        fields = ["id", "factory_number", "name", "func"]
        read_only_fields = ["id"]


class DefinitionSerializer(serializers.ModelSerializer):
    device = DeviceSerializer()

    class Meta:
        model = Definition
        fields = ["id", "device", "number"]
        read_only_fields = ["id", "device"]

class UserGroupDefinitionSerializer(serializers.ModelSerializer):
    definitions = DefinitionSerializer(many=True, read_only=True)

    class Meta:
        model = User
        fields = [
            'definitions', 'id', 'first_name', 'last_name',
            'phone', 'email', 'username', 'address', 'apartment',
            'fias', 'balance', 'ws_status', 'tariff_plan',
            'start_datetime_pp', 'end_datetime_pp'
        ]
        read_only_fields = [
            'definition', 'id', 'first_name', 'last_name',
            'phone', 'email', 'username', 'address', 'apartment',
            'fias', 'balance', 'ws_status', 'tariff_plan',
            'start_datetime_pp', 'end_datetime_pp'
        ]


class OtherDefinitionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Definition
        fields = ['device', 'number', 'user']

