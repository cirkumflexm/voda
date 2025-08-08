from django.contrib.auth.hashers import check_password
from django.db.models import Q
from drf_spectacular.utils import extend_schema, OpenApiResponse, extend_schema_view
from rest_framework import generics, viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import IsAuthenticated, BasePermission
from rest_framework.response import Response
from rest_framework.views import APIView

from rest_framework_simplejwt.tokens import RefreshToken

from django.contrib.auth import authenticate, logout, login
from rest_framework_simplejwt.views import TokenRefreshView
from re import sub, compile

from account.models import User
from account.tasks import create_account
from account.serializers import Authorization, AuthorizationResponseOk, Logout, \
    Registration, RegistrationResponseOk, DataSerializer, UserSerializer, UserSerializerGet

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


class LoginAPIView(APIView):

    @extend_schema(
        summary="Авторизация",
        request=Authorization,
        responses={
            200: AuthorizationResponseOk(),
            401: OpenApiResponse()
        }
    )
    def post(self, request):
        _login = request.data.get('login')
        password = request.data.get('password')
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


class RegistrationAPIView(APIView):
    @extend_schema(
        summary="Регистрация",
        description="только ру номера: +7",
        request=Registration,
        responses={
            200: RegistrationResponseOk(),
            401: OpenApiResponse()
        }
    )
    def post(self, request) -> Response:
        try:
            first_name = request.data.get('first_name', '')
            last_name = request.data.get('last_name', '')
            email = request.data.get('email', '')
            phone = request.data.get('phone', '')
            apartment = request.data.get('apartment')
            fias = request.data.get('fias')
            tariff_plan = request.data.get('tariff_plan')
            address = request.data.get('address')
            if not (first_name and last_name and phone):
                return Response("Данные введены некорректно.", status=400)
            phone = sub(PHONE_COMPILE, '', phone)
            if User.objects.filter(phone=int(phone)).exists():
                return Response("Номер уже зарегистрирован.", status=400)
            elif email and User.objects.filter(email=email).exists():
                return Response("Почта уже зарегистрирована.", status=400)
            create_account.delay(
                phone=int(phone), email=email,
                first_name=first_name, last_name=last_name,
                apartment=apartment, fias=fias,
                address=address, tariff_plan=tariff_plan
            )
        except Exception as ex:
            print(ex)
            return Response("Введите номер телефона", status=400)
        return Response("Ok", status=200)


class LogoutAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Выход",
        request=Logout,
        responses={
            200: AuthorizationResponseOk(),
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
    queryset = User.objects.select_related("tariff_plan") \
        .filter(groups__id=3).order_by('id')
    permission_classes = [IsAuthenticated]
    pagination_class = Pagination

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
        return RegistrationAPIView.post(request)

    def get_queryset(self):
        request = self.__dict__.get("request")
        if request and request.user.groups.filter(id=3).exists():
            return [self.request.user]
        return super().get_queryset()

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return UserSerializerGet
        else:
            return UserSerializer

    def partial_update(self, request, *args, **kw) -> Response:
        print(request.data, args, kw)
        return super().partial_update(request, *args, **kw)


@extend_schema(summary="Получить данные пользователя")
class DataView(generics.RetrieveAPIView):
    queryset = User.objects.filter(groups__id=3)
    serializer_class = DataSerializer
    lookup_field = "personal_account"