
from rest_framework import serializers

from .models import *


class DeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Device
        fields = ["id", "factory_number", "name", "func"]
        read_only_fields = ['id']

class EncoardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Encoard
        fields = ["device", "number", "user"]
        read_only_fields = ['id']
