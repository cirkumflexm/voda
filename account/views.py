from uuid import uuid4

from celery.result import AsyncResult
from django.contrib.auth.hashers import check_password
from django.core.cache import cache
from django.db.models import Q, F
from drf_spectacular.utils import extend_schema, OpenApiResponse, extend_schema_view
from rest_framework import generics, viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.pagination import LimitOffsetPagination
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
    RegistrationUser, RegistrationUserResponse, DataSerializer, UserSerializerPost, UserSerializerGet, UserSerializerPatch, \
    DoubleAuthenticationSerializer, TargetResposneSerializer, FastAuthUserSerializer, AuthorizationOperator
from address.models import Address
from config.celery import app
from tariff.models import TariffPlan

PHONE_COMPILE = compile(r'\D')


class Pagination(LimitOffsetPagination):
    max_limit = 150
    default_limit = 30


class PermissionGroup(BasePermission):
    def has_permission(self, request, view) -> bool | None:
        return request.user.groups.filter(id__in=(1, 2)).exists()


class UserPermissionGroup(PermissionGroup):
    def has_object_permission(self, request, view, obj) -> bool:
        if request.method != "GET" and not request.user.is_superuser:
            if obj.groups.filter(id__in=(1, 2)).exists():
                raise PermissionDenied()
        return True


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
    summary="Код подтверждения",
    request=DoubleAuthenticationSerializer,
    responses={
        200: AuthorizationResponse()
    }
)
class DoubleAuthentication(generics.GenericAPIView):
    def post(self, request: Request) -> Response:
        task = AsyncResult(request.data['id'], app=app)
        if task.ready():
            code, pa = task.result
            if code is None or code == request.data['code']:
                task.revoke()
                return release(request, User.objects.get(personal_account=pa))
        return Response("Код введен неверно.", status=403)


class LoginAPIView(APIView):

    @extend_schema(
        summary="Авторизация",
        request=Authorization,
        responses={
            200: TargetResposneSerializer()
        }
    )
    def post(self, request):
        serialize = Authorization(data=request.data)
        if serialize.is_valid():
            _login = serialize.data['login']
            password = serialize.data['password']
            if not (_login and password):
                return Response("Данные введены некорректно.", status=400)
            phone = sub(PHONE_COMPILE, "", _login)
            phone = int(phone) if phone else -1
            user = User.objects.filter(
                Q(username=_login) |
                Q(personal_account=_login) |
                Q(email=_login) |
                Q(phone=phone)
            ).first()
            if not (user and check_password(password, user.password)):
                return Response("Неправильно введен логин или пароль.", status=401)
            is_user = user.groups.filter(id=3).exists()
            result = send_sms_code.delay(user.phone, is_user, user.personal_account)
            return Response({
                "target": serialize.data['target'],
                "method": serialize.data['method'],
                "id": result.id,
            })
        else:
            return Response(serialize.error_messages, status=400)


class LoginOperator(APIView):

    @extend_schema(
        summary="Авторизация для операторов",
        request=AuthorizationOperator,
        responses={
            200: TargetResposneSerializer()
        }
    )
    def post(self, request: Request) -> Response:
        _login = request.data['login']
        password = request.data['password']
        user = User.objects.filter(username=_login).first()
        if not (user and check_password(password, user.password)):
            return Response("Неправильно введен логин или пароль.", status=401)
        return release(request, user)


@extend_schema(
    summary="Регистрация",
    description="только ру номера: +7",
    responses={
        200: RegistrationUserResponse(),
        401: OpenApiResponse()
    }
)
class RegistrationView(GenericAPIView):
    serializer_class = RegistrationUser

    def post(self, request) -> Response:
        serializer = RegistrationUser(data=request.data)
        assert serializer.is_valid(), serializer.error_messages
        assert not User.objects \
            .filter(phone=int(serializer.data['phone'].replace('+', ''))) \
            .exists(), "Номер уже зарегистрирован."
        address = Address(**serializer.data['address'])
        user = User(**(serializer.data | dict(address=address)))
        tariff_plan = TariffPlan.create_test_tariff_plan(user)
        registration_user_response = RegistrationUserResponse({
            'pa': address.pa,
            'new': not Address.objects \
                .filter(pa=int(address.pa)) \
                .exists(),
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
        .select_related("tariff_plan") \
        .select_related("address") \
        .annotate(pa=F('address')) \
        .filter(groups__id=3) \
        .order_by('id')
    permission_classes = [IsAuthenticated]
    pagination_class = Pagination
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
            return (User.objects
                .select_related("tariff_plan")
                .select_related("address")
                .get(id=self.request.user.id)
            ,)
        return super().get_queryset()

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