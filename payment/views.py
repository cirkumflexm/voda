
from django.core.cache import cache
from django.db.models import QuerySet
from django.http import JsonResponse, HttpResponse
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiResponse
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView

from account.models import User
from source.src.tools import Main
from payment.serializers import CheckRequest, CreateRequest, CreateResponse, CheckResponse
from .models import Payment
from .service import *


class Create(APIView):

    def get_permissions(self):
        if self.request.method == 'GET':
            return [IsAuthenticated()]
        return [AllowAny()]

    @extend_schema(
        summary="Создать и получить ссылку для оплаты [Authenticated]",
        description="номер карты - 5555555555554477",
        responses={
            200: CreateResponse()
        }
    )
    def get(self, request) -> Response:
        if not request.user.groups.filter(id=3).exists():
            return Response("", status=403)
        return self.create(request)

    @extend_schema(
        summary="Создать и получить ссылку для оплаты [No authenticated]",
        description="номер карты - 5555555555554477",
        request=CreateRequest,
        responses={
            200: CreateResponse()
        }
    )
    def post(self, request) -> Response:
        request.user = QuerySet(User).filter(personal_account=request.data["pa"]).first()
        if not request.user:
            return Response("Пользователь не найден.", status=400)
        if not request.user.groups.filter(id=3).exists():
            return Response("", status=403)
        return self.create(request)

    def create(self, request) -> Response:
        try:
            __payment_id = QuerySet(Payment).filter(user=request.user).count()
            __response = create_payment(
                num=__payment_id + 1,
                price=request.user.tariff_plan.price,
                tariff_name=request.user.tariff_plan.name,
                full_name=f"{request.user.last_name} {request.user.first_name}",
                user_phone=f"+7{request.user.phone}",
                user_email=request.user.email,
                user_id=request.user.id,
                tariff_id=request.user.tariff_plan.id,
                return_url="https://v.zesu.ru/",
                currency="RUB"
            )
            return Response(__response["response_data"])
        except ApiError as ex:
            return Response(
                ex.content["code"],
                status=ex.HTTP_CODE
            )


class Check(APIView):

    @extend_schema(
        summary="Проверить оплату",
        request=CheckRequest,
        description="раз в 5 секунд, иначе 429",
        responses={
            200: CheckResponse()
        }
    )
    def post(self, request) -> HttpResponse:
        try:
            payment_id = request.data["payment_id"]
            assert not cache.get(payment_id), "Too many requests"
            cache.set(payment_id, "1", timeout=5)
            __response = find_payment(payment_id=payment_id)
            request.user = QuerySet(User).get(id=__response["metadata"]["user_id"])
            if not request.user.groups.filter(id=3).exists():
                return Response("", status=403)
            if QuerySet(Payment).filter(payment=payment_id).exists():
                return Response("Платеж не найден", status=404)
            __payment_id = QuerySet(Payment).filter(user=request.user).count()
            if __response["response_data"]["status"] == "waiting_for_capture":
                __response = capture_payment(payment_id=payment_id)
                _main = Main(request.user, payment_id)
                _main.add_balance(float(__response["amount_value"]))
                _main.activate()
                request.user.save(force_update=[
                    'balance', 'start_datetime_pp', 'end_datetime_pp'
                ])
            if 'metadata' in __response:
                del __response["metadata"]
            return Response(__response)
        except ApiError as ex:
            return Response(
                ex.content["code"],
                status=ex.HTTP_CODE
            )
        except AssertionError as ex:
            return Response(f"{ex}", status=429)
