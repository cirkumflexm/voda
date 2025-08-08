from django.db.models import Q
from rest_framework import viewsets
from rest_framework import generics
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.exceptions import PermissionDenied

from account.models import User
from .serializers import DeviceSerializer, DefinitionSerializer, UserGroupDefinitionSerializer, \
    OtherDefinitionSerializer
from device.models import Device, Definition


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
    http_method_names = ['get', 'post', 'patch', 'head', 'options']


class DefinitionView(viewsets.ModelViewSet):
    queryset = User.objects.filter(groups__id=3).order_by('id')
    permission_classes = [IsAuthenticated, PermissionGroup]
    pagination_class = Pagination
    http_method_names = ['get', 'post', 'patch', 'head', 'options']

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return UserGroupDefinitionSerializer
        else:
            return OtherDefinitionSerializer