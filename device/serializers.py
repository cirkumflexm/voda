
from rest_framework import serializers

from account.serializers import UserSerializerGet
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
    device = DeviceSerializer(read_only=True)

    class Meta:
        model = Definition
        fields = ['id', 'device', 'number']
        read_only_fields = ['id', 'device', 'number']


class DefinitionSerializerSet(serializers.ModelSerializer):
    pa = Pa.pa
    apartment = serializers.CharField(label="Квартира", default="1")

    class Meta:
        model = Definition
        fields = ['id', 'device', 'number', 'pa', 'apartment']
        read_only_fields = ['id', 'apartment']


class SwitchSerializer(serializers.Serializer):
    pa = Pa.pa
    action = serializers.ChoiceField(choices=(('on', 'включить'), ('off', 'выключить')), label="Действие")


class SwitchResponseSerializer(serializers.Serializer):
    status = serializers.CharField(label="Успешно!", default="Успешно!")