from rest_framework import serializers

from promo.models import Promo
from tariff.serializers import CutTariffSerializer


class PromoCheck(serializers.ModelSerializer):
    tariff_plan = CutTariffSerializer(read_only=True, label="Тариф")
    status = serializers.CharField(default="Успешно!", label="Успешно!")

    class Meta:
        model = Promo
        fields = ('uuid', 'status', 'tariff_plan')
        read_only_fields = ('uuid', 'status', 'tariff_plan')