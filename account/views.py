from django.contrib.auth.hashers import check_password
from django.db.models import Q
from drf_spectacular.utils import extend_schema, OpenApiResponse
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from rest_framework_simplejwt.tokens import RefreshToken

from django.contrib.auth import authenticate, logout, login
from rest_framework_simplejwt.views import TokenRefreshView
from re import sub, compile

from account.models import User
from account.tasks import create_account
from account.serializers import Authorization, AuthorizationResponseOk, Logout, \
    Registration, RegistrationResponseOk


PHONE_COMPILE = compile(r'\D')


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
    def post(self, request):
        try:
            first_name = request.data.get('first_name', '')
            last_name = request.data.get('last_name', '')
            email = request.data.get('email', '')
            phone = request.data.get('phone', '')
            if not (first_name and last_name and phone):
                return Response("Данные введены некорректно.", status=400)
            phone = sub(PHONE_COMPILE, '', phone)
            if User.objects.filter(phone=int(phone)).exists():
                return Response("Номер уже зарегистрирован.", status=400)
            elif email and User.objects.filter(email=email).exists():
                return Response("Почта уже зарегистрирована.", status=400)
            create_account.delay(
                int(phone), email,
                first_name, last_name
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