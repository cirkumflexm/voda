from functools import lru_cache
from hashlib import sha256
from json import loads
from random import randint
from typing import Any, cast

from celery.result import AsyncResult
from django.contrib.auth import login, logout
from django.core.cache import cache
from django.db.models import F, Q
from django.http.request import HttpRequest
from drf_spectacular.utils import OpenApiParameter, extend_schema
from phonenumber_field.serializerfields import PhoneNumberField
from redis import Redis
from rest_framework import generics, serializers, views, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.token_blacklist.models import (
    BlacklistedToken,
    OutstandingToken,
)
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView

from account.models import User
from account.serializers import (
    AuthorizationResponse,
    DataSerializer,
    DoubleAuthSerializer,
    MethodCodeChoices,
    TargetCodeChoices,
    TariffPlanSerializerWithoutPa,
    UserSerializer,
    UserSerializerGet,
    UserSerializerPatch,
)
from account.tasks import send_sms_code
from address.models import Address
from config.tools import Pa, assertion_response
from device.models import Definition
from tariff.models import TariffPlan


def release(request: HttpRequest, user: User) -> Response:
    login(request, user)
    refresh = RefreshToken.for_user(user)
    refresh.payload.update({
        'user_id': getattr(user, 'id'),
        'username': user.username
    })
    return Response({
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }, status=200)


def remote_logout(user: User) -> None:
    tokens = OutstandingToken.objects.filter(user=user)
    entries = [
        BlacklistedToken(token=token)
        for token in tokens
    ]
    if entries:
        BlacklistedToken.objects.bulk_create(
            entries,
            ignore_conflicts=True
        )


class NextDoneView(views.APIView):

    class NDVRequestSerializer(serializers.Serializer):
        id = serializers.UUIDField(label="Id")

    @extend_schema(
        summary="Завершение регистрации",
        request=NDVRequestSerializer,
        responses={200: AuthorizationResponse()}
    )
    @assertion_response
    def post(self, request: Request) -> Response:
        nds = self.NDVRequestSerializer(data=request.data)
        assert nds.is_valid(), nds.error_messages
        data = cast(dict[str, Any], nds.validated_data)
        key = f'activate:{data['id']}'
        result: Any = cache.get(key)
        if result is None:
            return Response("ID недействителен.", status=403)
        cache.delete(key)
        result = loads(result)
        user = User.objects \
                .filter(id=result['user_id'], is_verified=True).first()
        assert user, "Регистрация не завершена"
        response = release(request._request, user)
        return response


class DoubleAuthentication(generics.GenericAPIView):

    @extend_schema(
        summary="Код подтверждения [target=authcode]",
        request=DoubleAuthSerializer,
        responses={200: AuthorizationResponse()}
    )
    def post(self, request: Request) -> Response:
        das = DoubleAuthSerializer(data=request.data)
        assert das.is_valid(), das.error_messages
        data = cast(dict[str, Any], das.validated_data)
        code = sha256(data['code'].encode()).hexdigest()
        key = f'code:{data['id']}:{code}'
        result: Any = cache.get(key)
        if result is None:
            return Response("Код введен неверно.", status=403)
        result = loads(result)
        cache.delete(key)
        user = User.objects.get(pk=result['user_id'])
        return release(request._request, user)


class DoubleRegistration(views.APIView):

    class DRResponseSerializer(serializers.Serializer):
        pa = serializers.CharField(label="Лицевой счет")
        new = serializers.BooleanField(label="Не активирован ранее")
        status = serializers.CharField(default="Успешно!", label="Статус")
        action = serializers.CharField(default="registration", label="Действие")
        id = serializers.UUIDField(label="Id операции")
        tariff_plan = TariffPlanSerializerWithoutPa(read_only=True, label="Тариф")
        method = serializers.CharField(label="Метод", default="payment")

    @extend_schema(
        summary="Код подтверждения [target=regcode]",
        request=DoubleAuthSerializer,
        responses={200: DRResponseSerializer()}
    )
    @assertion_response
    def post(self, request: Request) -> Response:
        das = DoubleAuthSerializer(data=request.data)
        assert das.is_valid(), das.error_messages
        data = cast(dict[str, Any], das.validated_data)
        code = sha256(data['code'].encode()).hexdigest()
        key = f'code:{data['id']}:{code}'
        result: Any = cache.get(key)
        if result is None:
            return Response("Код введен неверно.", status=403)
        cache.delete(key)
        cache.set(f'activate:{data['id']}', result, timeout=300)
        result = loads(result)
        user = User.objects.get(id=result['user_id'])
        TariffPlan.create_user_planse(user)
        user.is_verified = True
        user.save(update_fields=('is_verified', 'tariff_plan', 'next_tariff_plan'))
        rurs = self.DRResponseSerializer({
            'pa': getattr(user, 'address_id'),
            'new': user.is_new,
            'tariff_plan': user.tariff_plan,
            'id': data['id']
        })
        return Response(rurs.data, status=200)


class LoginAPIView(APIView):

    class LAVRequestSerializer(serializers.Serializer):
        login = serializers.CharField(label="Логин")
        target = serializers.ChoiceField(
            default=TargetCodeChoices.DEFAULT_AUTHCODE,
            choices=TargetCodeChoices.CHOICES,
            label=TargetCodeChoices.LABEL,
        )
        method = MethodCodeChoices.METHOD

    class LAVResponseSerializer(serializers.Serializer):
        id = serializers.UUIDField(label="Id задачи")
        target = serializers.ChoiceField(
            default=TargetCodeChoices.DEFAULT_REGCODE,
            choices=TargetCodeChoices.CHOICES,
            label=TargetCodeChoices.LABEL,
        )
        method = MethodCodeChoices.METHOD
        pa = Pa.pa

    @extend_schema(
        summary="Авторизация",
        request=LAVRequestSerializer,
        responses={200: LAVResponseSerializer()}
    )
    @assertion_response
    def post(self, request):
        serialize = self.LAVRequestSerializer(data=request.data)
        assert serialize.is_valid(), serialize.error_messages
        data = cast(dict[str, Any], serialize.validated_data)
        user = User.objects.filter(
            Q(address_id=data['login']) | Q(phone=data['login'])
        ).first()
        if user is None:
            return Response("Пользователь не найден", status=404)
        result: AsyncResult = send_sms_code.delay(user.phone, user.pk)
        response = self.LAVResponseSerializer(data={
            "target": "authcode",
            "pa": getattr(user, 'address_id'),
            "method": data['method'],
            "id": result.id,
        })
        response.is_valid()
        return Response(response.data)


@extend_schema(
    description="""
/account/next/ указываем номер квартиры и pa (/address/list/). отправляем смс

/accont/registration/submit/ вводим полученный код из смс. далее получаем id задачи (не uuid тарифа)

/payment/action/ вводим id и метод - payment. получаем confirmation_token; или id для тестов.
ссылка для оплаты: https://yoomoney.ru/payments/checkout/confirmation?orderId={id}

смс придет на тестовый api /account/temp-test/get_sms_list
"""
)
class RegistrationView(views.APIView):

    class RVSerializerRequest(serializers.Serializer):

        class PhoneAutoGenerator:
            def __str__(self) -> str:
                return "+79" + "".join(
                        str(randint(0, 9)) for _ in range(9))

        phone = PhoneNumberField(
            label="Телефон", region='RU',
            default=PhoneAutoGenerator()
        )
        pa = Pa.pa
        target = serializers.ChoiceField(
            default=TargetCodeChoices.DEFAULT_REGCODE,
            choices=TargetCodeChoices.CHOICES,
            label=TargetCodeChoices.LABEL,
        )
        method = MethodCodeChoices.METHOD

    class RVSerializerResponse(RVSerializerRequest):
        phone = None
        id = serializers.UUIDField()

    @extend_schema(
        summary="Регистрация",
        request=RVSerializerRequest,
        responses={200: RVSerializerResponse()}
    )
    @assertion_response
    def post(self, request) -> Response:
        serializer = self.RVSerializerRequest(data=request.data)
        assert serializer.is_valid(), serializer.error_messages
        data = cast(dict[str, Any], serializer.validated_data)
        address = Address.objects.filter(pa=data['pa']).first()
        assert address, "Адреса не существует."
        definition = Definition.objects.filter(address_id=data['pa']).first()
        assert definition, "К сожалению адрес не подключен к системе."
        phone = str(data['phone'])
        assert not User.objects.filter(phone=phone).exists(), \
                "Номер телефона уже существует."
        user = User.objects.filter(address_id=address.pa).first()
        if user:
            if user.is_verified:
                assert user.payment_method is None and not user.auto_payment, \
                        "Вы не можете зарегестрироваться на активный аккаунт."
                remote_logout(user)
        else:
            user = User.objects.create(
                address=address,
                definition=definition,
                phone=phone,
                username = f'u{address.pa}'
            )
            user.groups.add(3)
        result: AsyncResult = send_sms_code.delay(phone, user.pk)
        response = self.RVSerializerResponse(data={
            "pa": address.pa,
            "target": data['target'],
            "method": data['method'],
            "id": result.id
        })
        response.is_valid()
        return Response(response.data)


class LogoutAPIView(views.APIView):
    permission_classes = [IsAuthenticated]

    class LAVRequestSerializer(serializers.Serializer):
        refresh = serializers.CharField()

    @extend_schema(
        summary="Выход",
        request=LAVRequestSerializer,
        responses={200: AuthorizationResponse()}
    )
    def post(self, request: Request):
        lavr = self.LAVRequestSerializer(data=request.data)
        assert lavr.is_valid(), lavr.error_messages
        data = cast(dict[str, Any], lavr.validated_data)
        try:
            token = RefreshToken(data['refresh'])
            token.blacklist()
            logout(request._request)
        except Exception:
            return Response("Неверный Refresh token", status=403)
        return Response("Выход успешен", status=200)


class Refresh(TokenRefreshView):
    permission_classes = [IsAuthenticated]


class UserView(viewsets.ModelViewSet):
    queryset = User.objects \
        .filter(groups__id=3) \
        .annotate(pa=F('address__pa')) \
        .order_by('id')
    permission_classes = [IsAuthenticated]
    lookup_field = "pa"
    http_method_names = ['get', 'patch']

    def list(self, *args, **kw):
        return super().list(*args, **kw)

    @extend_schema(
        summary="Получить пользователя",
        parameters=[OpenApiParameter(name="pa", type=str, location="path")],
    )
    def retrieve(self, *args, **kw):
        return super().retrieve(*args, **kw)

    @extend_schema(
        summary="Изменить данные пользователя",
        parameters=[OpenApiParameter(name="pa", type=str, location="path")],
    )
    def partial_update(self, *args, **kw):
        return super().partial_update(*args, **kw)

    def get_queryset(self):
        if self.request.user.groups.filter(id=3).exists():
            self.queryset = self.queryset \
                .select_related('address') \
                .filter(id=self.request.user.pk)
        return self.queryset.annotate(pa=F('address_id'))

    def get_serializer_class(self):
        if self.action == 'list':
            return UserSerializerGet
        elif self.action == 'partial_update':
            return UserSerializerPatch
        else:
            return UserSerializer


@extend_schema(summary="Получить данные пользователя")
class DataView(generics.RetrieveAPIView):
    queryset = User.objects \
        .annotate(pa=F('address')) \
        .filter(groups__id=3) \
        .values('pa', 'ws_status', 'start_datetime_pp', 'end_datetime_pp')
    serializer_class = DataSerializer
    lookup_field = "pa"


@extend_schema(summary="Получить данные пользователя")
class MyUserView(generics.RetrieveAPIView):
    queryset = User.objects \
        .annotate(pa=F('address')) \
        .filter(groups__id=3) \
        .values('pa', 'ws_status', 'start_datetime_pp', 'end_datetime_pp', 'is_new')
    serializer_class = DataSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs) -> Response:
        data = self.get_queryset().get(pk=request.user.pk)
        data['pa'] = f"{data['pa']:0>12}"
        return Response(data)


# --------------------------


class TempGetCodesList(views.APIView):

    @lru_cache(1)
    @staticmethod
    def get_redis():
        return Redis()

    @extend_schema(responses={}, request={})
    def get(self, *args, **kw) -> Response:
        redis = self.get_redis()
        result: Any = redis.lrange("sms_list", 0, -1)
        return Response([_.decode() for _ in result][::-1])


class FastAuthUser(generics.GenericAPIView):
    class FAUSerializer(serializers.Serializer):
        id = serializers.CharField(label='ID пользователя')
    serializer_class = FAUSerializer

    def post(self, request: Request) -> Response:
        data = cast(dict[str, Any], request.data)
        user = User.objects.filter(id=data['id']).first()
        if user is None:
            return Response("Пользователь не найден", status=404)
        return release(request._request, user)
