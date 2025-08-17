
from rest_framework import serializers

from .models import *


class TariffPlanSerializer(serializers.ModelSerializer):

    class Meta:
        model = TariffPlan
        fields = ['id', 'name', 'price', 'archive', 'unit_measurement', 'owner', 'is_test']
        read_only_fields = ['id', 'is_test']
        allows = ["GET", "POST", "PATCH"]


class TariffChoicesSerializer(serializers.ModelSerializer):

    class Meta:
        model = TariffPlan
        fields = ['name', 'price', 'archive', 'unit_measurement', 'is_test']
        read_only_fields = ['id', 'name', 'price', 'archive', 'unit_measurement', 'is_test']
        allows = ['GET']
