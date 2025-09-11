from django.db.models import F
from drf_spectacular.utils import extend_schema
from rest_framework import viewsets
from rest_framework.generics import GenericAPIView
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from account.models import User
from config.permissions import get_permission_group, OnlyOperatorOrAdmin
from device.models import Device, Definition
from .common import set_ws_status
from .serializers import DeviceSerializer, UserGroupDefinitionSerializer, \
    DefinitionSerializerGet, DefinitionSerializerSet, SwitchSerializer, SwitchResponseSerializer


class Pagination(LimitOffsetPagination):
    max_limit = 150
    default_limit = 30


class DeviceView(viewsets.ModelViewSet):
    queryset = Device.objects.order_by('id')
    serializer_class = DeviceSerializer
    permission_classes = [IsAuthenticated, get_permission_group(1, 2)]
    pagination_class = Pagination
    http_method_names = ['get', 'post', 'patch']


class DefinitionView(viewsets.ModelViewSet):
    queryset = Definition.objects \
        .select_related('user', 'device', 'user__address') \
        .annotate(pa=F('user__address')) \
        .order_by('id')
    permission_classes = [IsAuthenticated, get_permission_group(1, 2)]
    pagination_class = Pagination
    http_method_names = ['get', 'post', 'patch']\

    def get_serializer_class(self):
        if self.action == 'list':
            return UserGroupDefinitionSerializer
        elif self.action == 'retrieve':
            return DefinitionSerializerGet
        else:
            return DefinitionSerializerSet

    def get_queryset(self):
        if self.action == 'list':
            return User.objects.filter(groups__id=3).order_by('id')
        return super().get_queryset()


@extend_schema(
    summary="Вкл/Выкл",
    parameters=[SwitchSerializer]
)
class Switch(GenericAPIView):
    serializer_class = SwitchResponseSerializer
    permission_classes = [IsAuthenticated, OnlyOperatorOrAdmin]

    def get(self, request: Request) -> Response:
        action, pa = request.query_params.dict().values()
        user = User.objects.get(address_id=int(pa))
        set_ws_status(user, action == "on")
        return Response(self.get_serializer().data)