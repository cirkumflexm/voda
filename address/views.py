
from rest_framework import viewsets
from rest_framework.pagination import LimitOffsetPagination
from .models import Address
from .serializers import AddressSerializeList, AddressSerializeOther
from account.models import User



class Pagination(LimitOffsetPagination):
    max_limit = 150
    default_limit = 30


class AddressView(viewsets.ModelViewSet):
    # queryset = User.objects.select_related('address')
    queryset = Address.objects.all()
    pagination_class = Pagination
    # permission_classes = [permissions.IsAuthenticated, HighLevelLpansOrRead]
    lookup_field = 'pa'

    def get_serializer_class(self) -> type[AddressSerializeList | AddressSerializeOther]:
        if self.action == 'list':
            return AddressSerializeList
        return AddressSerializeOther
