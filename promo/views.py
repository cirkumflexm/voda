from uuid import uuid4

from django.db.models import QuerySet
from drf_spectacular.utils import extend_schema
from rest_framework.generics import RetrieveAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from config.permissions import get_permission_group
from promo.models import Promo
from promo.serializers import PromoCheck
from tariff.models import TariffPlan


@extend_schema(summary="Промокоды")
class PromoCheckView(RetrieveAPIView):
    queryset = Promo.objects.only(
        'uuid', 'tariff_plan__uuid',
        'tariff_plan__name', 'tariff_plan__price',
        'tariff_plan__unit_measurement'
    )
    serializer_class = PromoCheck
    permission_classes = [IsAuthenticated, get_permission_group(3)]

    def get(self, request: Request, promo: str) -> Response:
        data = self.queryset \
            .filter(label=promo) \
            .first()
        request.user.tariff_plan = data.tariff_plan
        request.user.tariffs.add(request.user.tariff_plan)
        serializer = self.get_serializer(data)
        return Response(data=serializer.data)