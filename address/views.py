from django.contrib.postgres.search import TrigramSimilarity
from django.db.models import QuerySet
from django.db.models.functions import Cast
from drf_spectacular.utils import extend_schema
from rest_framework.generics import GenericAPIView, ListAPIView
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.request import Request
from rest_framework.response import Response

from .models import Address
from .serializers import AddressSerializeBase, AddressSerializeOther, AddressSerializeList, RequestQuery
from account.models import User



class Pagination(LimitOffsetPagination):
    max_limit = 150
    default_limit = 30


@extend_schema(
    summary="Список адресов",
    parameters=[RequestQuery]
)
class AddressView(ListAPIView):
    queryset = Address.objects \
        .filter(apartment='') \
        .only('pa', 'join')
    serializer_class = AddressSerializeList
    lookup_field = "query"
    pagination_class = None

    def get_queryset(self) -> QuerySet:
        query = self.request.GET.get('query', 'а')
        return self.queryset \
            .annotate(similarity=TrigramSimilarity('join', query)) \
            .order_by('-similarity')[:10]
