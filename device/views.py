
from rest_framework import viewsets
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import BasePermission, IsAuthenticated

from account.models import User
from device.models import Device, Definition
from .serializers import DeviceSerializer, UserGroupDefinitionSerializer, \
    DefinitionSerializerGet, DefinitionSerializerSet


class Pagination(LimitOffsetPagination):
    max_limit = 150
    default_limit = 30


class PermissionGroup(BasePermission):
    def has_permission(self, request, view) -> bool:
        return request.user.groups.filter(id__in=(1, 2)).exists()


class DeviceView(viewsets.ModelViewSet):
    queryset = Device.objects.order_by('id')
    serializer_class = DeviceSerializer
    permission_classes = [IsAuthenticated, PermissionGroup]
    pagination_class = Pagination
    http_method_names = ['get', 'post', 'patch']


class DefinitionView(viewsets.ModelViewSet):
    queryset = Definition.objects \
        .select_related('user', 'device').order_by('id')
    permission_classes = [IsAuthenticated, PermissionGroup]
    pagination_class = Pagination
    http_method_names = ['get', 'post', 'patch']

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
