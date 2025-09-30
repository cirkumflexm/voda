from uuid import uuid4

from celery import chain
from django.contrib.auth import login
from django.core.cache import cache
from django.http import HttpResponse
from rest_framework.request import Request
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.generics import GenericAPIView

from account.tasks import task_create_account
from account.models import User, RegistrationCacheModel
from config.tools import assertion_response
from payment.serializers import CheckRequest, CreateRequest, CreateResponse, CheckResponse, CreateByIdParamsSerializer
from tariff.serializers import TariffPlanSerializer
from .models import Payment as ModelPayment
from .service import Payment, ApiError, create_payment, find_payment
from .tasks import check, complete


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
        request.user = User.objects.filter(personal_account=request.data["pa"]).first()
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
            return Response(
                ex.content["code"],
                status=ex.HTTP_CODE
            )


@extend_schema(
    summary="Создать оплату по id",
    parameters=[CreateByIdParamsSerializer],
    responses={
        200: CreateResponse()
    }
)
class CreateForTestTariff(GenericAPIView):

    @assertion_response
    def get(self, request: Request) -> Response:
        serialize = CreateByIdParamsSerializer(data={
            "id": request.GET['id'],
            "method": request.GET['method'],
        })
        assert serialize.is_valid(), serialize.error_messages
        reg_cache_model: RegistrationCacheModel = cache.get(serialize.data['id'])
        if not reg_cache_model:
            return Response(status=403)
        assert reg_cache_model.method == serialize.data['method'], "Метод не определен."
        __response = create_payment(
            num=1,
            price=reg_cache_model.tariff_plan.price,
            tariff_name=reg_cache_model.tariff_plan.name,
            full_name=f"{reg_cache_model.user.last_name} {reg_cache_model.user.first_name}",
            user_phone=reg_cache_model.user.phone,
            user_email=reg_cache_model.user.email,
            user_id=reg_cache_model.user.address.pa,
            tariff_id=reg_cache_model.user.tariff_plan.id,
            currency="RUB"
        )
        __result = __response["response_data"]
        __task = chain(
            check.s(__result['id'], reg_cache_model_id=serialize.data['id']),
            task_create_account.s(serialize.data['id'], __result['id'])
        )
        __task.apply_async()
        __result["tariff"] = TariffPlanSerializer(reg_cache_model.user.tariff_plan).data
        __result["pa"] = reg_cache_model.user.address.pa
        return Response(__result)


@extend_schema(
    summary="Проверить статус оплаты",
    responses={
        200: CheckResponse()
    }
)
class Check(GenericAPIView):
    serializer_class = CheckRequest

    def post(self, request) -> HttpResponse:
        try:
            payment_id = request.data["payment_id"]
            __response = find_payment(payment_id=payment_id)
            request.user = User.objects.get(id=__response["metadata"]["user_id"])
            if not request.user.groups.filter(id=3).exists():
                return Response("", status=403)
            if ModelPayment.objects.filter(payment=payment_id).exists():
                return Response("Платеж не найден", status=404)
            if 'metadata' in __response:
                del __response["metadata"]
            return Response(__response)
        except ApiError as ex:
            return Response(
                ex.content["code"],
                status=ex.HTTP_CODE
            )
