from itertools import product

from django.db import IntegrityError
from drf_spectacular.utils import extend_schema
from rest_framework import viewsets
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from account.models import User
from address.models import Address
from config.permissions import OnlyOperatorOrAdmin
from config.tools import assertion_response
from device.models import Device, Definition
from .common import set_ws_status
from .serializers import DeviceSerializer, UserGroupDefinitionSerializer, \
    DefinitionSerializerGet, DefinitionSerializerSet, SwitchSerializer, SwitchResponseSerializer


class DeviceView(viewsets.ModelViewSet):
    queryset = Device.objects.order_by('id')
    serializer_class = DeviceSerializer
    permission_classes = [OnlyOperatorOrAdmin, IsAuthenticated]
    http_method_names = ['get', 'post', 'patch']


class DefinitionView(viewsets.ModelViewSet):
    queryset = Definition.objects \
        .order_by('id') \
        .values(
            'address', 'number', 'id',
            'device__name', 'device__factory_number',
            'device__func', 'device__id'
        )
    http_method_names = ['get', 'post', 'patch']
    permission_classes = [OnlyOperatorOrAdmin, IsAuthenticated]

    def list(self, request, *args, **kwargs):
        queryset = super().get_queryset()
        users = User.objects \
            .filter(address__in=[_['address'] for _ in self.queryset]) \
            .values(
            'phone', 'address__join', 'address', 'ws_status',
                'start_datetime_pp', 'end_datetime_pp',
                'is_new', 'tariff_plan__uuid', 'tariff_plan__name',
                'tariff_plan__price', 'tariff_plan__unit_measurement',
                'tariff_plan__is_test', 'next_tariff_plan__uuid',
                'next_tariff_plan__name', 'next_tariff_plan__price',
                'next_tariff_plan__unit_measurement', 'next_tariff_plan__is_test'
            )
        results = []
        for definition, user in product(queryset, users):
            if user['address'] == definition['address']:
                definition = {**definition}
                user = {**user}
                user['pa'] = f"{user['address']:0>12}"
                user['address'] = user.pop('address__join')
                user['tariff_plan'] = {
                    'uuid': user.pop('tariff_plan__uuid'),
                    'name': user.pop('tariff_plan__name'),
                    'price': user.pop('tariff_plan__price'),
                    'unit_measurement': user.pop('tariff_plan__unit_measurement'),
                    'is_test': user.pop('tariff_plan__is_test'),
                }
                user['next_tariff_plan'] = {
                    'uuid': user.pop('next_tariff_plan__uuid'),
                    'name': user.pop('next_tariff_plan__name'),
                    'price': user.pop('next_tariff_plan__price'),
                    'unit_measurement': user.pop('next_tariff_plan__unit_measurement'),
                    'is_test': user.pop('next_tariff_plan__is_test'),
                }
                definition['device'] = [{
                    'id': definition.pop('device__id'),
                    'name': definition.pop('device__name'),
                    'factory_number': definition.pop('device__factory_number'),
                    'func': definition.pop('device__func'),
                }]
                if hasattr(user, 'definition'):
                    user['definition']['device'] += definition['device']
                else:
                    user['definition'] = definition
                results.append(user)
        return Response(data=results)

    @assertion_response
    def create(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            address = Address.objects.get(pk=serializer.data['pa'])
            address.pk = None
            address.apartment = serializer.data['apartment']
            address.pa = address.get_pa()
            address.join = address.get_join()
            address.save()
            Definition.objects.create(
                device_id=serializer.data['device'],
                number=serializer.data['number'],
                address=address
            )
            serializer.data['pa'] = address.pa
            serializer.is_valid()
            return Response(serializer.data)
        except IntegrityError:
            raise AssertionError("Адрес уже существует.")

    def get_serializer_class(self):
        if self.action == 'list':
            return UserGroupDefinitionSerializer
        elif self.action == 'retrieve':
            return DefinitionSerializerGet
        else:
            return DefinitionSerializerSet


@extend_schema(
    summary="Вкл/Выкл",
    parameters=[SwitchSerializer]
)
class Switch(GenericAPIView):
    serializer_class = SwitchResponseSerializer
    permission_classes = [IsAuthenticated, OnlyOperatorOrAdmin]

    def get(self, request: Request) -> Response:
        action, pa = request.query_params.dict().values()
        set_ws_status(pa, action == "on")
        return Response(self.get_serializer().data)