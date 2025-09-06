from rest_framework import serializers

from promo.models import Promo


class PromoCheck(serializers.ModelSerializer):
    class Meta:
        model = Promo
        fields = ('uuid',)
        read_only_fields = ('uuid',)