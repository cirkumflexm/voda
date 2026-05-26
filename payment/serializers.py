
from rest_framework import serializers

from config.tools import Pa
from tariff.serializers import TariffPlanSerializer


class ResponseData(serializers.Serializer):
    status = serializers.CharField()


class OnAutoPaymentSerializer(serializers.Serializer):
    status = serializers.CharField(
        default='Успешно!',
        read_only=True
    )


class CreateRequest(serializers.Serializer):
    pa = serializers.CharField()


class Amount(serializers.Serializer):
    currency = serializers.CharField()
    confirmation_url = serializers.CharField()


class Confirmation(serializers.Serializer):
    type = serializers.CharField()
    confirmation_url = serializers.CharField()


class CreateResponse(serializers.Serializer):
    id = serializers.CharField()
    description = serializers.CharField()
    created_at = serializers.CharField()
    amount = Amount()
    confirmation = Confirmation()
    tariff = TariffPlanSerializer(read_only=True)
    pa = Pa.pa

    class Meta:
        fields = ["id", "description", "created_at", "amount", "confirmation", "name", "price", "unit_measurement", "pa"]


class CreateByIdParamsSerializer(serializers.Serializer):
    id = serializers.UUIDField(label="Id метода")
    method = serializers.CharField(label="Метод")
