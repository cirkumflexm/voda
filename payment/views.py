
from django.core.cache import cache
from django.db.models import QuerySet
from django.http import JsonResponse, HttpResponse
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from source.src.tools import crediting_funds
from payment.serializers import CheckRequest
from .models import Payment
from .service import *


class Create(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Создать и получить ссылку для оплаты",
        description="номер карты - 5555555555554477"
    )
    def get(self, request) -> Response:
        if not request.user.groups.filter(id=3).exists():
            return Response("", status=403)
        try:
            __payment_id = QuerySet(Payment).filter(user=request.user).count()
            __response = create_payment(
                num = __payment_id+1,
                price = request.user.tariff_plan.price,
                tariff_name = request.user.tariff_plan.name,
                full_name = f"{request.user.last_name} {request.user.first_name}",
                user_phone = "",
                user_email = request.user.email,
                user_id = request.user.id,
                tariff_id = request.user.tariff_plan.id,
                return_url = "https://v.zesu.ru/",
                currency = "RUB"
            )
            return Response(__response["response_data"])
        except ApiError as ex:
            return Response(
                ex.content["code"],
                status=ex.HTTP_CODE
            )


class Check(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Проверить оплату",
        request=CheckRequest,
        description="раз в 5 секунд, иначе 429"
    )
    def post(self, request) -> HttpResponse:
        if not request.user.groups.filter(id=3).exists():
            return Response("", status=403)
        try:
            payment_id = request.data["payment_id"]
            assert not cache.get(payment_id), "Too many requests"
            cache.set(payment_id, "1", timeout=5)
            __payment_id = QuerySet(Payment).filter(user=request.user).count()
            __response = find_payment(payment_id=payment_id)
            if __response["response_data"]["status"] == "waiting_for_capture":
                __response = capture_payment(payment_id=payment_id)
                crediting_funds(request.user, __response["amount_value"])
            return Response(__response)
        except ApiError as ex:
            return Response(
                ex.content["code"],
                status=ex.HTTP_CODE
            )
        except AssertionError as ex:
            return Response(f"{ex}", status=429)
