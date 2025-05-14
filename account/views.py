
from drf_spectacular.utils import extend_schema, OpenApiResponse
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from rest_framework_simplejwt.tokens import RefreshToken

from django.contrib.auth import authenticate, logout, login
from rest_framework_simplejwt.views import TokenRefreshView

from account.serializers import Authorization, AuthorizationResponseOk, Logout


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
        username = request.data.get('personal_account', "")
        password = request.data.get('password', "")
        user = authenticate(username=username, password=password)
        if user is None:
            return Response("Неправильно введен счет или пароль.", status=401)
        else:
            login(request, user)
            refresh = RefreshToken.for_user(user)
            refresh.payload.update(
                {
                    'user_id': user.id,
                    'username': user.username
                }
            )
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }, status=200)


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