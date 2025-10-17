from copy import copy

from rest_framework import permissions
from rest_framework.request import Request
from rest_framework.viewsets import ViewSet


class OnlyOperatorOrAdmin(permissions.BasePermission):
    def has_permission(self, request: Request, view: ViewSet) -> bool:
        return not request.user.groups.filter(id=3).exists()


class HighLevelLpansOrRead(OnlyOperatorOrAdmin):
    def has_permission(self, request: Request, view: ViewSet) -> bool:
        return super().has_permission(request, view) or view.request.method == 'GET'


class PermissionGroup(permissions.BasePermission):
    _id__in = None

    def has_permission(self, request, view) -> bool:
        return request.user.groups.filter(id__in=self._id__in).exists()


def get_permission_group(*ids: int) -> type[PermissionGroup]:
    permission_class = copy(PermissionGroup)
    permission_class._id__in = ids
    return permission_class