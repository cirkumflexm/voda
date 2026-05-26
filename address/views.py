from django.contrib.postgres.search import TrigramDistance
from django.db.models import QuerySet
from drf_spectacular.utils import extend_schema
from rest_framework.generics import ListAPIView
from rest_framework.pagination import LimitOffsetPagination
from .models import Address
from .serializers import AddressSerializeList, RequestQuery


class Pagination(LimitOffsetPagination):
    max_limit = 150
    default_limit = 30


@extend_schema(
    summary="Список адресов",
    parameters=[RequestQuery]
)
class AddressView(ListAPIView):
    queryset = Address.objects \
        .only('pa', 'line')
    serializer_class = AddressSerializeList
    lookup_field = "query"
    pagination_class = None

    def get_queryset(self) -> QuerySet:
        query = self.request.GET.get('query', '')
        queryset = self.queryset \
            .annotate(distance=TrigramDistance('line', query)) \
            .order_by('distance')[:10]
        print(queryset.query)
        return queryset

