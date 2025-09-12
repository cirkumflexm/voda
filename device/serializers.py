
from rest_framework import serializers

from account.models import User
from account.serializers import UserSerializerGet, UserSerializeBase
from config.tools import Pa
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
        
        
class UserGroupDefinitionSerializer(UserSerializerGet, Pa):
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


class SwitchSerializer(serializers.Serializer):
    pa = Pa.pa
    action = serializers.ChoiceField(choices=(('on', 'включить'), ('off', 'выключить')), label="Действие")


class SwitchResponseSerializer(serializers.Serializer):
    status = serializers.CharField(label="Успешно!", default="Успешно!")