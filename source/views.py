from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import viewsets
from rest_framework import generics
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from django.db.models import QuerySet

from account.models import User

from .serializers import UserSerializer, TariffPlanSerializer, DataSerializer
from .models import TariffPlan


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
        return request.method in ["GET", "POST", "PUT"]


class DataPermissionGroup(PermissionGroup):
    def has_object_permission(self, request, view, obj) -> bool:
        print(view, obj)
        return "GET" == request.method


@extend_schema_view(
    list=extend_schema(
        summary="Получить список пользователей",
    ),
    retrieve=extend_schema(
        summary="Получить пользователя",
    ),
    update=extend_schema(exclude=True),
    partial_update=extend_schema(exclude=True),
    create=extend_schema(
        summary="Добавить пользователя",
    ),
    destroy=extend_schema(exclude=True)
)
class UserView(viewsets.ModelViewSet):
    queryset = QuerySet(User).filter(groups__id=3).select_related("tariff_plan").all()
    serializer_class = UserSerializer
    permission_classes = [UserPermissionGroup, IsAuthenticated]
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

    def get_queryset(self):
        request = self.__dict__.get("request")
        if request and request.user.groups.filter(id=3).exists():
            return [self.request.user]
        return super().get_queryset()


@extend_schema_view(
    list=extend_schema(
        summary="Получить список тарифов",
    ),
    retrieve=extend_schema(
        summary="Получить тариф",
    ),
    update=extend_schema(
        summary="Изменить признак активности",
    ),
    partial_update=extend_schema(exclude=True),
    create=extend_schema(
        summary="Добавить тариф",
    ),
    destroy=extend_schema(exclude=True)
)
class TariffPlanView(viewsets.ModelViewSet):
    queryset = QuerySet(TariffPlan).all()
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
        request = self.__dict__.get("request")
        if request and request.user.groups.filter(id=3).exists():
            __tariff_plan = request.user.tariff_plan
            return [request.user.tariff_plan] if __tariff_plan else []
        return super().get_queryset()


@extend_schema(summary="Получить данные пользователя")
class DataView(generics.RetrieveAPIView):
    queryset = QuerySet(User).filter(groups__id=3)
    serializer_class = DataSerializer
    lookup_field = "personal_account"
