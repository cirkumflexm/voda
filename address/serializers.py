
from rest_framework import serializers

from account.models import User
from address.models import Address
from config.tools import GetPaBase


class AddressSerializeBase(serializers.ModelSerializer):
    join = serializers.SerializerMethodField()
    pa = serializers.CharField(label="Лицевой счет", read_only=True)

    class Meta:
        model = Address
        fields = ['pa', 'join']
        read_only_fields = ('pa', 'join')

    @staticmethod
    def get_join(model: Address) -> str:
        return str(model)


class RequestQuery(serializers.Serializer):
    query = serializers.CharField(label="Поиск", required=False)


class AddressSerializeList(serializers.ModelSerializer, GetPaBase):
    address = serializers.SerializerMethodField()

    class Meta:
        model = Address
        fields = ('address', 'pa')
        read_only_fields = ('address', 'pa')

    @staticmethod
    def get_address(model: Address) -> str:
        return str(model.join)


class ForRegistrationAddress(serializers.ModelSerializer):

    class Meta:
        model = Address
        fields = ('apartment', 'pa')


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
