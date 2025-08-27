
from rest_framework import serializers

from account.models import User
from account.serializers import UserSerializerGet, UserSerializeBase
from config.tools import GetPaBase
from .models import *


class DeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Device
        fields = ["id", "factory_number", "name", "func"]
        read_only_fields = ["id"]


class DefinitionSerializerList(serializers.ModelSerializer):
    device = DeviceSerializer(read_only=True)

    class Meta:
        model = Definition
        fields = ["id", "device", "number"]
        read_only_fields = ["id", "device", "number"]
        
        
class UserGroupDefinitionSerializer(UserSerializerGet, GetPaBase):
    definitions = DefinitionSerializerList(many=True, read_only=True)

    class Meta(UserSerializerGet.Meta):
        fields = UserSerializerGet.Meta.fields + ['definitions']


class DefinitionSerializerGet(serializers.ModelSerializer):
    user = UserSerializerGet(read_only=True)
    device = DeviceSerializer(read_only=True)

    class Meta:
        model = Definition
        fields = ['id', 'device', 'number', 'user']
        read_only_fields = ['id', 'device', 'number', 'user']


class DefinitionSerializerSet(serializers.ModelSerializer):
    class Meta:
        model = Definition
        fields = ['id', 'device', 'number', 'user']
        read_only_fields = ['id']