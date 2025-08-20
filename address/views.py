from django.db.models import QuerySet
from rest_framework import viewsets, permissions
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.request import Request

from config.permissions import HighLevelLpansOrRead
from .serializers import AddressSerialize
from account.models import User


class Pagination(LimitOffsetPagination):
    max_limit = 150
    default_limit = 30


class AddressView(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.filter(groups__id=3)
    pagination_class = Pagination
    serializer_class = AddressSerialize
    permission_classes = [permissions.IsAuthenticated, HighLevelLpansOrRead]
    lookup_field = 'personal_account'

    def get_queryset(self) -> QuerySet:
        queryset = self.queryset
        if self.request.user.groups.filter(id=3).exists():
            queryset = queryset.filter(id=self.request.user.id)
        return queryset \
            .values('personal_account', 'address', 'apartment', 'first_name', 'last_name') \
            .order_by('id')