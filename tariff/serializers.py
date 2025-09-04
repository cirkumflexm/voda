
from rest_framework import serializers

from account.models import User
from config.tools import GetPa, Pa
from .models import *


class TariffPlanSerializer(serializers.ModelSerializer, GetPa):
    pa = GetPa.pa

    class Meta:
        model = TariffPlan
        fields = ['uuid', 'name', 'price', 'archive', 'unit_measurement', 'pa', 'is_test']
        read_only_fields = ['uuid', 'is_test', 'pa']
        allows = ["GET", "POST", "PATCH"]


class TariffPlanSerializerWithoutOwner(TariffPlanSerializer):
    class Meta(TariffPlanSerializer.Meta):
        fields = TariffPlanSerializer.Meta.fields
        allows = ['GET']


class TariffChoicesSerializer(serializers.ModelSerializer):

    class Meta:
        model = TariffPlan
        fields = ['uuid', 'name', 'price', 'archive', 'unit_measurement', 'is_test']
        read_only_fields = ['uuid', 'id', 'name', 'price', 'archive', 'unit_measurement', 'is_test']
        allows = ['GET']


class ActivationTestTariffSerializer(serializers.Serializer):
    pa = serializers.CharField()
    tariff = serializers.IntegerField(min_value=1, required=False, allow_null=True)

    class Meta:
        fields = '__all__'
        read_only_fields = '__all__'