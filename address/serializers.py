
from rest_framework import serializers

from account.models import User
from address.models import Address
from config.tools import GetPa, Pa


class AddressSerializeBase(serializers.ModelSerializer, GetPa):
    join = serializers.SerializerMethodField()
    pa = GetPa.pa

    class Meta:
        model = Address
        fields = ['pa', 'join']
        read_only_fields = ('pa', 'join')

    @staticmethod
    def get_join(model: Address) -> str:
        return str(model)


class RequestQuery(serializers.Serializer):
    query = serializers.CharField(label="Поиск", required=False)


class AddressSerializeList(serializers.ModelSerializer, GetPa):
    address = serializers.SerializerMethodField(label="Адрес")
    pa = GetPa.pa

    class Meta:
        model = Address
        fields = ('address', 'pa')
        read_only_fields = ('address', 'pa')

    @staticmethod
    def get_address(model: Address) -> str:
        return str(model.join)


class AddressSerializeChange(AddressSerializeBase):
    class Meta(AddressSerializeBase.Meta):
        fields = AddressSerializeBase.Meta.fields + [
            'street', 'house', 'building',
            'apartment', 'fias'
        ]


class AddressSerializeOther(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = '__all__'
