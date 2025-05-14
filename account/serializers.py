
from rest_framework import serializers

from account.models import User


class Authorization(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["personal_account", "password"]


class AuthorizationResponseOk(serializers.Serializer):
    refresh = serializers.CharField()
    access = serializers.CharField()


class Logout(serializers.Serializer):
    refresh = serializers.CharField()