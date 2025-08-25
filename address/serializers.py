
from rest_framework import serializers

from account.models import User
from address.models import Address


class AddressSerializeList(serializers.ModelSerializer):
    join = serializers.SerializerMethodField()

    class Meta:
        model = Address
        fields = ('pa', 'join')
        read_only_fields = ('pa', 'join')

    @staticmethod
    def get_join(model: Address) -> str:
        return str(model)


class AddressSerializeOther(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = '__all__'
