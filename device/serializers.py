
from rest_framework import serializers

from account.serializers import UserSerializerGet
from config.tools import GetPa, Pa
from device.models import Definition, DefinitionAddress, Device


class DeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Device
        fields = ["id", "number", "name"]
        read_only_fields = ["id"]


class DefinitionSerializerList(serializers.ModelSerializer):
    device = DeviceSerializer(read_only=True)

    class Meta:
        model = Definition
        fields = ["id", "device", "port"]
        read_only_fields = ["id", "device", "port"]
        
        
class UserGroupDefinitionSerializer(UserSerializerGet, Pa):
    definitions = DefinitionSerializerList(many=True, read_only=True)

    class Meta(UserSerializerGet.Meta):
        fields = UserSerializerGet.Meta.fields + ['definitions']


class DefinitionSerializerGet(serializers.ModelSerializer):
    device = DeviceSerializer(read_only=True)

    class Meta:
        model = Definition
        fields = ['id', 'device', 'port']
        read_only_fields = ['id', 'device', 'port']


class DefinitionSerializerSet(serializers.ModelSerializer):
    pa = Pa.pa
    apartment = serializers.CharField(label="Квартира", default="1")

    class Meta:
        model = Definition
        fields = ['id', 'device', 'port', 'pa', 'apartment']
        read_only_fields = ['id', 'apartment']


class SwitchSerializer(serializers.Serializer):
    pa = Pa.pa
    action = serializers.ChoiceField(choices=(('on', 'включить'), ('off', 'выключить')), label="Действие")


class SwitchResponseSerializer(serializers.Serializer):
    status = serializers.CharField(label="Успешно!", default="Успешно!")


class ApartmentAddressDefaultQuery(serializers.Serializer):
    pa = serializers.CharField(label="Лицевой счет", required=False)


class AddressSerializeList(serializers.ModelSerializer, GetPa):
    address = serializers.SerializerMethodField(label="Адрес")
    pa = GetPa.pa

    class Meta:
        model = DefinitionAddress
        fields = ('address', 'pa')
        read_only_fields = ('address', 'pa')

    @staticmethod
    def get_address(model: DefinitionAddress) -> str:
        return str(model.apartment_value)



