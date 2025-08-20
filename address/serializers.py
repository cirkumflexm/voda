
from rest_framework import serializers

from account.models import User


class AddressSerialize(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'personal_account', 'address',
            'apartment', 'first_name', 'last_name'
        ]