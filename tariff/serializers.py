
from rest_framework import serializers

from .models import *


class TariffPlanSerializer(serializers.ModelSerializer):

    class Meta:
        model = TariffPlan
        fields = ['id', 'name', 'price', 'archive', 'unit_measurement', 'owner']
        allows = ["GET", "POST", "PATCH"]

    def __init__(self, *args, **kw) -> None:
        super().__init__(*args, **kw)
        if kw.get("context"):
            __request = kw.get("context", {}).get('request')
            try:
                assert __request
                assert not __request.user.groups.filter(id=1).exists()
                assert kw.get("context", {}).get("request") and kw["context"]["request"].method == "PATCH"
                self.Meta.read_only_fields = ['id', 'name', 'price', 'unit_measurement', 'owner']
            except AssertionError:
                self.Meta.read_only_fields = []


class TariffChoicesSerializer(serializers.ModelSerializer):

    class Meta:
        model = TariffPlan
        fields = ['name', 'price', 'archive', 'unit_measurement']
        read_only_fields = ['id', 'name', 'price', 'archive', 'unit_measurement']
        allows = ['GET']
