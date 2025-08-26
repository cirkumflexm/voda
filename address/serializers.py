
from rest_framework import serializers

from account.models import User
from address.models import Address


class AddressSerializeBase(serializers.ModelSerializer):
    join = serializers.SerializerMethodField()

    class Meta:
        model = Address
        fields = ['pa', 'join']
        read_only_fields = ('pa', 'join')

    @staticmethod
    def get_join(model: Address) -> str:
        return str(model)


class AddressSerializeList(serializers.ModelSerializer):
    address = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('address',)
        read_only_fields = ('address',)

    @staticmethod
    def get_address(model: User) -> str:
        return str(model.address or '')


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
