
from rest_framework import serializers

from tariff.serializers import TariffPlanSerializer


class CheckRequest(serializers.Serializer):
    payment_id = serializers.CharField()

    class Meta:
        fields = ["payment_id"]


class ResponseData(serializers.Serializer):
    status = serializers.CharField()


class CheckResponse(serializers.Serializer):
    response_data = ResponseData()

    class Meta:
        fields = ["response_data"]


class CreateRequest(serializers.Serializer):
    pa = serializers.CharField()
    class Meta:
        fields = ["pa"]


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

    class Meta:
        fields = ["id", "description", "created_at", "amount", "confirmation", "name", "price", "unit_measurement"]


class CreateByIdParamsSerializer(serializers.Serializer):
    id = serializers.UUIDField(label="Id метода")
    method = serializers.CharField(label="Метод")
