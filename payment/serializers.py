
from rest_framework import serializers


class CheckRequest(serializers.Serializer):
    payment_id = serializers.CharField()

    class Meta:
        fields = ["payment_id"]
