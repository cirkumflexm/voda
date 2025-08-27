from django.db.models import F
from django.http import JsonResponse
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import viewsets
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.generics import GenericAPIView

from account.models import User
from payment.views import Create
from .serializers import TariffPlanSerializer, TariffChoicesSerializer, ActivationTestTariffSerializer
from .models import TariffPlan
from .src.tools import Main, CustomException


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


class TariffPlanPermissionGroup(PermissionGroup):
    def has_object_permission(self, request, view, obj) -> bool:
        return request.method in ["GET", "POST", "PATCH"]


@extend_schema_view(
    list=extend_schema(
        summary="Получить список тарифов",
    ),
    retrieve=extend_schema(
        summary="Получить тариф",
    ),
    update=extend_schema(exclude=True),
    partial_update=extend_schema(
        summary="Изменить признак активности",
    ),
    create=extend_schema(
        summary="Добавить тариф",
    ),
    destroy=extend_schema(exclude=True)
)
class TariffPlanView(viewsets.ModelViewSet):
    queryset = TariffPlan.objects \
        .select_related('owner') \
        .annotate(pa=F('owner__address')) \
        .order_by('id')
    serializer_class = TariffPlanSerializer
    permission_classes = [TariffPlanPermissionGroup, IsAuthenticated]
    pagination_class = Pagination
    lookup_field = "uuid"

    def __init__(self, **kw) -> None:
        super().__init__(**kw)
        self.description = """
            Список тарифов:
            Методы: 
            Для Администратор:
            чтение, изменение(только параметр archive), добавление, удаление
            Для Оператор:
            чтение, изменение(только параметр ws_status), добавление
            Для пользователей:
            чтение
        """

    def get_queryset(self):
        if self.request and self.request.user.groups.filter(id=3).exists():
            __tariff_plan = self.request.user.tariff_plan
            return [self.request.user.tariff_plan] if __tariff_plan else []
        return super().get_queryset()


@extend_schema_view(
    list=extend_schema(
        summary="Получить список тарифов пользователя",
    ),
    retrieve=extend_schema(exclude=True),
    update=extend_schema(exclude=True),
    partial_update=extend_schema(exclude=True),
    create=extend_schema(exclude=True),
    destroy=extend_schema(exclude=True)
)
class TariffChoices(viewsets.ModelViewSet):
    queryset = TariffPlan.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = TariffChoicesSerializer

    def get_queryset(self):
        return TariffPlan.objects.filter(owner=self.request.user, archive=False)


class Activate(GenericAPIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(summary="Активация тарифа")
    def get(self, request) -> Response:
        Main(request.user).activate()
        request.user.save()
        request.user.tariff_plan.save()
        return Response("Ok", 200)


class ActivationTestTariff(GenericAPIView):
    serializer_class = ActivationTestTariffSerializer

    @extend_schema(summary="Активация тестового тарифа")
    def post(self, request: Request) -> Response | JsonResponse:
        try:
            serializer = ActivationTestTariffSerializer(data=request.data)
            assert serializer.is_valid(), str(serializer.error_messages)
            user = User.objects.get(personal_account=serializer.data['pa'])
            assert user.is_new, "Пользователь не является новым"
            test_tariff = user.tariff_choices.get(is_test=True, archive=False)
            user.tariff_plan = test_tariff
            if serializer.data.get('tariff'):
                tariff = user.tariff_choices.filter(id=serializer.data['tariff']).first()
                assert tariff, "Тариф не принадлежит пользователю"
                user.next_tariff_plan = tariff
            user.save()
            return Create.create(user, request)
        except AssertionError as ex:
            return Response(ex, status=400)
