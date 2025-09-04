
from rest_framework import permissions
from rest_framework.request import Request
from rest_framework.viewsets import ViewSet


class OnlyOperatorOrAdmin(permissions.BasePermission):
    def has_permission(self, request: Request, view: ViewSet) -> bool:
        return not request.user.groups.filter(id=3).exists()


class HighLevelLpansOrRead(OnlyOperatorOrAdmin):
    def has_permission(self, request: Request, view: ViewSet) -> bool:
        return super().has_permission(request, view) or view.request.method == 'GET'
