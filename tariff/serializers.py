
from rest_framework import serializers

from .models import TariffPlan


class TariffPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = TariffPlan
        fields = ['uuid', 'name', 'price', 'archive', 'unit_measurement', 'is_test']
        read_only_fields = ['uuid', 'is_test']
        allows = ["GET", "POST", "PATCH"]


class TariffPlanSerializerWithoutPa(serializers.ModelSerializer):
    class Meta:
        model = TariffPlan
        fields = ['uuid', 'name', 'price', 'archive', 'unit_measurement', 'is_test']
        read_only_fields = ['uuid', 'is_test']
        allows = ["GET", "POST", "PATCH"]


class TariffChoicesSerializer(serializers.ModelSerializer):

    class Meta:
        model = TariffPlan
        fields = ['uuid', 'name', 'price', 'archive', 'unit_measurement', 'is_test']
        read_only_fields = ['uuid', 'id', 'name', 'price', 'archive', 'unit_measurement', 'is_test']
        allows = ['GET']


class ActivationTestTariffSerializer(serializers.Serializer):
    tariff = serializers.IntegerField(min_value=1, required=False, allow_null=True)

    class Meta:
        fields = '__all__'
        read_only_fields = '__all__'


class CutTariffSerializer(TariffPlanSerializer):
    class Meta(TariffPlanSerializer.Meta):
        fields = ['uuid', 'name', 'price', 'unit_measurement']
        read_only_fields = ['uuid', 'is_test']