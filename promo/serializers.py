from rest_framework import serializers

from promo.models import Promo
from tariff.serializers import TariffChoicesSerializer


class PromoCheck(serializers.ModelSerializer):
    tariff_plan = TariffChoicesSerializer(read_only=True, label="Тариф")

    class Meta:
        model = Promo
        fields = ('uuid', 'tariff_plan')
        read_only_fields = ('uuid', 'tariff_plan')