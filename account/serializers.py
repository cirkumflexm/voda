
from rest_framework import serializers

from account.models import User


class Authorization(serializers.ModelSerializer):
    login = serializers.CharField()
    class Meta:
        model = User
        fields = ["login", "password"]


class Registration(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["phone", "email", "first_name", "last_name"]


class AuthorizationResponseOk(serializers.Serializer):
    refresh = serializers.CharField()
    access = serializers.CharField()


class RegistrationResponseOk(serializers.Serializer):
    status = serializers.CharField(default="Ok")


class Logout(serializers.Serializer):
    refresh = serializers.CharField()