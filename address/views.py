
from rest_framework.generics import ListAPIView
from rest_framework.pagination import LimitOffsetPagination
from .models import Address
from .serializers import AddressSerializeBase, AddressSerializeOther, AddressSerializeList
from account.models import User



class Pagination(LimitOffsetPagination):
    max_limit = 150
    default_limit = 30


class AddressView(ListAPIView):
    queryset = User.objects.select_related('address') \
        .filter(address__isnull=False)
    pagination_class = Pagination
    serializer_class = AddressSerializeList
