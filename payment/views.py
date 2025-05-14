
from django.core.cache import cache
from django.db.models import QuerySet
from django.http import JsonResponse
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from source.src.tools import crediting_funds
from .models import Payment
from .service import *



class Create(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Создать и получить ссылку для оплаты",
    )
    def get(self, request) -> JsonResponse:
        if request.user.groups.filter(id=2).exists():
            return JsonResponse({}, status=403)
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
                return_url = "http://127.0.0.1:8000",
                currency = "RUB"
            )
            return JsonResponse({"status": "ok", "data": __response["response_data"]})
        except ApiError as ex:
            return JsonResponse(
                {"status": "error", "data": ex.content["code"]},
                status=ex.HTTP_CODE
            )


class Check(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Проверить оплату и получить результат",
        description="раз в 5 секунд, иначе 429"
    )
    def post(self, request) -> JsonResponse:
        if request.user.groups.filter(id=2).exists():
            return JsonResponse({}, status=403)
        try:
            payment_id = (request.GET.dict() | request.POST.dict())["payment_id"]
            assert not cache.get(payment_id), "Too many requests"
            cache.set(payment_id, "1", timeout=5)
            __payment_id = QuerySet(Payment).filter(user=request.user).count()
            __response = find_payment(payment_id=payment_id)
            if __response["response_data"]["status"] == "waiting_for_capture":
                __response = capture_payment(payment_id=payment_id)
                crediting_funds(request.user, __response["amount_value"])
            return JsonResponse({"status": "ok", "data": __response["response_data"]})
        except ApiError as ex:
            return JsonResponse(
                {"status": "error", "data": ex.content["code"]},
                status=ex.HTTP_CODE
            )
        except AssertionError as ex:
            return JsonResponse({"status": "error", "data": f"{ex}"}, status=429)