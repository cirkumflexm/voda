from django.db.models import QuerySet
from drf_spectacular.utils import extend_schema
from rest_framework.generics import GenericAPIView
from rest_framework.request import Request
from rest_framework.response import Response

from promo.models import Promo
from promo.serializers import PromoCheck


@extend_schema(summary="Промокоды")
class PromoCheckView(GenericAPIView):
    queryset = Promo.objects
    serializer_class = PromoCheck

    def get(self, request, promo: str) -> Response:
        data = self.queryset \
            .filter(label=promo) \
            .values(
            'uuid', 'tariff_plan__uuid', 'tariff_plan__name', 'tariff_plan__price',
                'tariff_plan__archive', 'tariff_plan__unit_measurement', 'tariff_plan__is_test'
            ) \
            .first()
        serializer = PromoCheck(data=data)
        return Response(data=data)