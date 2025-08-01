from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import viewsets
from rest_framework import generics
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.exceptions import PermissionDenied

from .serializers import DeviceSerializer, EncoardSerializer
from device.models import Device, Encoard


class Pagination(LimitOffsetPagination):
    max_limit = 150
    default_limit = 30


class PermissionGroup(BasePermission):
    def has_permission(self, request, view) -> bool:
        return request.user.groups.filter(id__in=(1, 2)).exists()


class DeviceView(viewsets.ModelViewSet):
    queryset = Device.objects.all()
    serializer_class = DeviceSerializer
    permission_classes = [IsAuthenticated, PermissionGroup]
    pagination_class = Pagination
    http_method_names = ['get', 'post', 'put', 'patch', 'head', 'options']


class EncoardView(viewsets.ModelViewSet):
    queryset = Encoard.objects.all()
    serializer_class = EncoardSerializer
    permission_classes = [IsAuthenticated, PermissionGroup]
    pagination_class = Pagination
    http_method_names = ['get', 'post', 'put', 'patch', 'head', 'options']