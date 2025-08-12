
from django.core.cache import cache
from django.db.models import QuerySet
from django.http import JsonResponse, HttpResponse
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiResponse
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView

from account.models import User
from payment.serializers import CheckRequest, CreateRequest, CreateResponse, CheckResponse
from tariff.models import TariffPlan
from tariff.serializers import TariffPlanSerializer
from .models import Payment
from .service import *
from .tasks import check


class Create(APIView):

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
        return self.create(request)

    @extend_schema(
        summary="Создать и получить ссылку для оплаты [No authenticated]",
        description="номер карты - 5555555555554477\n\nhttps://yookassa.ru/developers/payment-acceptance/integration-scenarios/widget/quick-start",
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
        return self.create(request)

    def create(self, request) -> Response:
        request.user.tariff_plan: TariffPlan

        try:
            __payment_id = QuerySet(Payment).filter(user=request.user).count()
            __response = create_payment(
                num=__payment_id + 1,
                price=request.user.tariff_plan.price,
                tariff_name=request.user.tariff_plan.name,
                full_name=f"{request.user.last_name} {request.user.first_name}",
                user_phone=f"+{request.user.phone}",
                user_email=request.user.email,
                user_id=request.user.id,
                tariff_id=request.user.tariff_plan.id,
                return_url="https://v.zesu.ru/",
                currency="RUB"
            )
            __result = __response["response_data"]
            check.delay(__result['id'], request.user.id)
            __result["tariff"] = TariffPlanSerializer(request.user.tariff_plan, context=request).data
            del __result["tariff"]['id']
            del __result["tariff"]['owner']
            del __result["tariff"]['archive']
            return Response(__result)
        except ApiError as ex:
            return Response(
                ex.content["code"],
                status=ex.HTTP_CODE
            )


class Check(APIView):

    @extend_schema(
        summary="Проверить статус оплаты",
        request=CheckRequest,
        responses={
            200: CheckResponse()
        }
    )
    def post(self, request) -> HttpResponse:
        try:
            payment_id = request.data["payment_id"]
            __response = find_payment(payment_id=payment_id)
            request.user = QuerySet(User).get(id=__response["metadata"]["user_id"])
            if not request.user.groups.filter(id=3).exists():
                return Response("", status=403)
            if QuerySet(Payment).filter(payment=payment_id).exists():
                return Response("Платеж не найден", status=404)
            if 'metadata' in __response:
                del __response["metadata"]
            return Response(__response)
        except ApiError as ex:
            return Response(
                ex.content["code"],
                status=ex.HTTP_CODE
            )
