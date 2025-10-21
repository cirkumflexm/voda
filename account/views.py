from uuid import uuid4

from celery.result import AsyncResult
from django.contrib.auth.hashers import check_password
from django.core.cache import cache
from django.db.models import Q, F
from drf_spectacular.utils import extend_schema, OpenApiResponse, extend_schema_view
from rest_framework import generics, viewsets
from rest_framework.permissions import IsAuthenticated, BasePermission
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import GenericAPIView

from rest_framework_simplejwt.tokens import RefreshToken

from django.http.request import HttpRequest
from django.contrib.auth import authenticate, logout, login
from rest_framework_simplejwt.views import TokenRefreshView
from re import sub, compile

from account.models import User, RegistrationCacheModel
from account.tasks import task_create_account, send_sms_code
from account.serializers import Authorization, AuthorizationResponse, Logout, \
    RegistrationUser, RegistrationUserResponse, DataSerializer, UserSerializerPost, UserSerializerGet, \
    UserSerializerPatch, \
    DoubleAuthenticationSerializer, ToDoubleNext, FastAuthUserSerializer, AuthorizationOperator, \
    RegistrationUserMeta, DoubleRegistrationSerializer, NextDoneId
from address.models import Address
from config.celery import app
from config.tools import assertion_response
from tariff.models import TariffPlan

PHONE_COMPILE = compile(r'\D')


def release(request: Request, user: User) -> Response:
    request: HttpRequest
    login(request, user)
    refresh = RefreshToken.for_user(user)
    refresh.payload.update({
        'user_id': user.id,
        'username': user.username
    })
    return Response({
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }, status=200)


@extend_schema(
    summary="Завершения регистрации",
    request=NextDoneId,
    responses={200: AuthorizationResponse()}
)
class NextDoneView(generics.GenericAPIView):

    @assertion_response
    def post(self, request: Request) -> Response:
        reg_cache_model = cache.get(request.data['id'])
        assert reg_cache_model, "Не правильный Id"
        user = User.objects.filter(phone=reg_cache_model.user.phone.replace('+', '')).first()
        assert user, "Регистрация не завершена"
        response = release(request, user)
        cache.delete(request.data['id'])
        return response


@extend_schema(
    summary="Код подтверждения [target=authcode]",
    request=DoubleAuthenticationSerializer,
    responses={200: AuthorizationResponse()}
)
class DoubleAuthentication(generics.GenericAPIView):
    def post(self, request: Request) -> Response:
        task = AsyncResult(request.data['id'], app=app)
        if task.ready():
            code, pa, target, phone = task.result
            if code is not None \
                    and code == request.data['code'] \
                    and target == 'authcode' \
                    and int(pa) == int(request.data['pa']):
                task.revoke()
                user = User.objects.get(address_id=pa)
                if user.phone != phone:
                    user.phone = phone
                    user.save(force_update=('phone',))
                return release(request, user)
        return Response("Код введен неверно.", status=403)


@extend_schema(
    summary="Код подтверждения [target=regcode]",
    request=DoubleRegistrationSerializer,
    responses={200: RegistrationUserResponse()}
)
class DoubleRegistration(generics.GenericAPIView):

    @assertion_response
    def post(self, request: Request) -> Response:
        task = AsyncResult(request.data['id'], app=app)
        if task.ready():
            code, pa, target, _ = task.result
            if code == request.data['code'] and target == 'regcode':
                task.revoke()
                address = Address.objects.filter(pk=pa).first()
                assert address, "К сожалению адрес не подключен к системе."
                meta_serializer = RegistrationUserMeta(data=request.data['meta'])
                assert meta_serializer.is_valid(), meta_serializer.errors
                user = User(
                    phone = meta_serializer.data['phone'],
                    first_name = "",
                    last_name = "",
                    address = address
                )
                tariff_plan = TariffPlan.create_test_tariff_plan(user)
                registration_user_response = RegistrationUserResponse({
                    'pa': address.pa,
                    'new': Address.objects \
                        .filter(pa=address.pa).exists(),
                    'tariff_plan': tariff_plan,
                    'id': uuid4()
                }).data
                cache.set(
                    registration_user_response['id'],
                    RegistrationCacheModel(
                        method=registration_user_response['method'],
                        user=user,
                        tariff_plan=tariff_plan
                    ),
                    timeout=3600*24
                )
                return Response(
                    registration_user_response,
                    status=200
                )
        return Response("Код введен неверно.", status=403)


class LoginAPIView(APIView):

    @extend_schema(
        summary="Авторизация",
        request=Authorization,
        responses={200: ToDoubleNext()}
    )
    @assertion_response
    def post(self, request):
        serialize = Authorization(data=request.data)
        assert serialize.is_valid(), serialize.errors
        _login = serialize.data['login']
        assert _login, "Данные введены некорректно."
        user = User.objects.filter(
            Q(address_id=int(_login)) | Q(phone=_login.replace('+', ''))
        ).first()
        assert user, "Пользователь не найден"
        result = send_sms_code.delay(user.phone, True, "authcode", user.address.pk)
        return Response({
            "target": "authcode",
            "method": serialize.data['method'],
            "id": result.id,
        })


class LoginOperator(APIView):

    @extend_schema(
        summary="Авторизация для операторов",
        request=AuthorizationOperator,
        responses={200: AuthorizationResponse()}
    )
    def post(self, request: Request) -> Response:
        _login = request.data['login']
        password = request.data['password']
        user = User.objects.filter(username=_login).first()
        assert user and check_password(password, user.password), \
            "Неправильно введен логин или пароль."
        return release(request, user)


@extend_schema(
    description="""
/account/next/ указываем номер квартиры и pa (/address/list/). отправляем смс 

/accont/registration/submit/ вводим полученный код из смс. далее получаем id задачи (не uuid тарифа)

/payment/action/ вводим id и метод - payment. получаем confirmation_token; или id для тестов.
ссылка для оплаты: https://yoomoney.ru/payments/checkout/confirmation?orderId={id}

смс придет на тестовый api /account/temp-test/get_sms_list
"""
)
class RegistrationView(GenericAPIView):
    serializer_class = RegistrationUser

    @assertion_response
    @extend_schema(summary="Регистрация", responses={200: ToDoubleNext()})
    def post(self, request) -> Response:
        serializer = RegistrationUser(data=request.data)
        assert serializer.is_valid(), serializer.error_messages
        address = Address.objects.filter(pa=serializer.data['pa']).first()
        assert address, "К сожалению адрес не подключен к системе."
        address.apartment = serializer.data['apartment']
        pa = address.get_pa()
        address = Address.objects.filter(pa=pa).first()
        assert address, "К сожалению адрес не подключен к системе."
        phone = serializer.data['phone'].replace('+', '')
        user = User.objects.filter(address=address).first()
        if user:
            assert not User.objects.filter(phone=phone).exists(), "Номер телефона уже существует."
            assert user.payment_method is None and not user.auto_payment, \
                "Вы не можете зарегестрироваться на активный аккаунт."
            result = send_sms_code.delay(phone, True, "authcode", pa)
        else:
            result = send_sms_code.delay(phone, True, "regcode", pa)
        response_serializer = ToDoubleNext(data={
            "pa": pa,
            "target": "authcode",
            "method": serializer.data['method'],
            "id": result.id
        })
        response_serializer.is_valid()
        return Response(response_serializer.data)


class LogoutAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Выход",
        request=Logout,
        responses={
            200: AuthorizationResponse(),
            401: OpenApiResponse()
        }
    )
    def post(self, request):
        refresh_token = request.data.get('refresh', '')
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
            logout(request)
        except Exception as ex:
            return Response("Неверный Refresh token", status=400)
        return Response("Выход успешен", status=200)


class Refresh(TokenRefreshView):
    permission_classes = [IsAuthenticated]


@extend_schema_view(
    list=extend_schema(
        summary="Получить список пользователей",
    ),
    retrieve=extend_schema(
        summary="Получить пользователя",
    ),
    update=extend_schema(exclude=True),
    partial_update=extend_schema(
        summary="Изменить данные пользователя"
    ),
    create=extend_schema(
        summary="Добавить пользователя",
    ),
    destroy=extend_schema(exclude=True)
)
class UserView(viewsets.ModelViewSet):
    queryset = User.objects \
        .filter(groups__id=3) \
        .order_by('id')
    permission_classes = [IsAuthenticated]
    lookup_field = "pa"

    def __init__(self, **kw) -> None:
        super().__init__(**kw)
        self.description = """
            Список пользователей:
            Методы: 
            Для Админ и Оператор:
            чтение, изменение, добавление, удаление
            Для пользователей:
            чтение
        """

    def create(self, request, *args, **kw) -> Response:
        return RegistrationView.post(self, request)

    def get_queryset(self):
        if self.request.user.groups.filter(id=3).exists():
            self.queryset = self.queryset \
                .select_related('address') \
                .filter(id=self.request.user.id)
        return self.queryset.annotate(pa=F('address_id'))

    def get_serializer_class(self):
        if self.action == 'list':
            return UserSerializerGet
        elif self.action == 'partial_update':
            return UserSerializerPatch
        else:
            return UserSerializerPost


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

from redis import Redis


redis = Redis(db=1)


class TempGetCodesList(APIView):

    @staticmethod
    def get(*args, **kw) -> Response:
        result = redis.lrange("sms_list", 0, -1)
        return Response([_.decode() for _ in result][::-1])


class FastAuthUser(GenericAPIView):
    serializer_class = FastAuthUserSerializer

    @staticmethod
    def post(request: Request) -> Response:
        _login = request.data['login']
        phone = sub(PHONE_COMPILE, "", _login)
        phone = int(phone) if phone else -1
        query = Q(username=_login) | Q(email=_login) | Q(phone=phone)
        if str.isnumeric(_login):
            query = query | Q(address=int(_login))
        user = User.objects.filter(query).first()
        if user is None:
            return Response("Пользователь не найден", status=400)
        return release(request, user)
