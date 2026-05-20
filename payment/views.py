from json import loads
import logging
from typing import Any, cast

from celery import chain
from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist
from drf_spectacular.utils import extend_schema
from functools import lru_cache
from redis import Redis
from rest_framework import serializers, views
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from account.models import User
from account.tasks import task_create_account
from config.tools import assertion_response
from payment.serializers import Amount, Confirmation, CreateRequest, \
        CreateResponse, OnAutoPaymentSerializer
from tariff.models import TariffPlan
from tariff.serializers import TariffPlanSerializer
from config.tools import Pa
from .models import Payment as ModelPayment
from .service import ApiError, create_payment
from .tasks import check, complete


@lru_cache(1)
def get_redis():
    return Redis()


class Create(GenericAPIView):

    def get_permissions(self):
        if self.request.method == 'GET':
            return [IsAuthenticated()]
        return [AllowAny()]

    @extend_schema(
        summary="Создать и получить ссылку для оплаты [Authenticated]",
        description="номер карты - 5555555555554477\n\nhttps://yookassa.ru/developers/payment-acceptance/integration-scenarios/widget/quick-start",
        responses={
            200: CreateResponse()
        }
    )
    def get(self, request) -> Response:
        if not request.user.groups.filter(id=3).exists():
            return Response("", status=403)
        return self.create(request.user, request)

    @extend_schema(
        summary="Создать и получить ссылку для оплаты [No authenticated]",
        description="номер карты - 5555555555554477\n\nhttps://yookassa.ru/developers/payment-acceptance/integration-scenarios/widget/quick-start\n\nhttps://yoomoney.ru/api-pages/v2/payment-confirm/epl?orderId=",
        request=CreateRequest,
        responses={
            200: CreateResponse()
        }
    )
    def post(self, request) -> Response:
        request.user = User.objects.filter(address_id=request.data["pa"]).first()
        if not request.user:
            return Response("Пользователь не найден.", status=400)
        if not request.user.groups.filter(id=3).exists():
            return Response("", status=403)
        return self.create(request.user, request)

    @staticmethod
    def create(user, request) -> Response:
        try:
            __payment_id = ModelPayment.objects.filter(user=user).count()
            __response = create_payment(
                num=__payment_id + 1,
                price=user.tariff_plan.price,
                tariff_name=user.tariff_plan.name,
                full_name=f"{user.last_name} {user.first_name}",
                user_phone=f"+{user.phone}",
                user_email=user.email,
                user_id=user.id,
                tariff_id=user.tariff_plan.id,
                currency="RUB"
            )
            __result = __response["response_data"]
            # __cache_id = uuid4()
            # cache.set(__cache_id, user)
            __task = chain(check.s(__result['id'], user.id), complete.s(__result['id'], user.id))
            __task.apply_async()
            __result["tariff"] = TariffPlanSerializer(user.tariff_plan, context=request).data
            return Response(__result)
        except ApiError as ex:
            logging.warning(ex)
            return Response(
                ex.content["code"],
                status=ex.HTTP_CODE
            )


class CreateForTestTariff(views.APIView):
    class CFTTRequestSerializer(serializers.Serializer):
        id = serializers.UUIDField(label="Id метода")
        method = serializers.CharField(label="Метод")

    class CFTTResponseSerializer(serializers.Serializer):
        id = serializers.CharField()
        description = serializers.CharField()
        created_at = serializers.CharField()
        amount = Amount()
        confirmation = Confirmation()
        tariff = TariffPlanSerializer(read_only=True)
        pa = Pa.pa

        class Meta:
            fields = ["id", "description", "created_at", "amount", "confirmation", "name", "price", "unit_measurement", "pa"]

    @extend_schema(
        summary="Создать оплату по id",
        request=CFTTRequestSerializer,
        responses={200: CFTTResponseSerializer()}
    )
    @assertion_response
    def post(self, request: Request) -> Response:
        serialize = self.CFTTRequestSerializer(data=request.data)
        assert serialize.is_valid(), serialize.error_messages
        data = cast(dict[str, Any], serialize.data)
        redis = get_redis()
        result: Any = redis.get(f'activate:{data['id']}')
        assert result, 'ID не существует.'
        result = loads(result)
        user = User.objects.get(id=result['user_id'])
        if user.tariff_plan is None:
            raise ObjectDoesNotExist('Текущий тариф пользователя не указан.')
        payment = create_payment(
            num=1,
            price=user.tariff_plan.price,
            tariff_name=user.tariff_plan.name,
            full_name=f"{user.last_name} {user.first_name}",
            user_phone=str(user.phone),
            user_email='',
            user_id=getattr(user, 'address_id'),
            tariff_id=user.tariff_plan.id,
            currency="RUB"
        )
        response_data = payment["response_data"]
        check.delay(payment_id=response_data['id'], user_id=result['user_id'])
        response_data["tariff"] = TariffPlanSerializer(user.tariff_plan).data
        response_data["pa"] = getattr(user, 'address_id')
        response = self.CFTTResponseSerializer(data=response_data)
        response.is_valid()
        return Response(data=response.data)


@extend_schema(
    summary="Отключить автооплату",
    responses={
        200: OnAutoPaymentSerializer()
    }
)
class OnAutoPayment(GenericAPIView):
    pagination_class = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        User.objects \
            .filter(pk=request.user.pk)\
            .update(payment_method=None)
        response_serializer = OnAutoPaymentSerializer(data={})
        response_serializer.is_valid()
        return Response(data=response_serializer.data)
