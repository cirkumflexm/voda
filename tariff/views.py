
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import viewsets
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from django.db.models import QuerySet
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import TariffPlanSerializer, TariffChoicesSerializer
from .models import TariffPlan
from .src.tools import Main


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
    queryset = TariffPlan.objects.order_by('id')
    serializer_class = TariffPlanSerializer
    permission_classes = [TariffPlanPermissionGroup, IsAuthenticated]
    pagination_class = Pagination

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


class Activate(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(summary="Активация тарифа")
    def get(self, request) -> Response:
        Main(request.user).activate()
        request.user.save()
        return Response("Ok", 200)
