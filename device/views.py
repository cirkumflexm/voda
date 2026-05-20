import asyncio
from base64 import b64encode
from itertools import product
from secrets import token_bytes
from typing import Iterable, TypedDict, cast
from json import loads
from asgiref.sync import async_to_sync
from dal.autocomplete import Select2QuerySetView

from django.shortcuts import redirect
from django.contrib.postgres.search import TrigramDistance
from django.db import IntegrityError
from django.db.models import QuerySet
from django.views.decorators.csrf import csrf_exempt
from drf_spectacular.utils import extend_schema
from rest_framework import viewsets
from rest_framework.generics import GenericAPIView, ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from django import http
from rest_framework.views import APIView
from playwright.async_api import async_playwright

from account.models import User
from address.models import Address
from config.permissions import OnlyOperatorOrAdmin
from config.tools import assertion_response
from device.models import DefinitionAddress, Device, Definition, LogDevice
from .common import set_ws_status
from .serializers import DeviceSerializer, AddressSerializeList, \
        UserGroupDefinitionSerializer, DefinitionSerializerGet, \
        DefinitionSerializerSet, SwitchSerializer, \
        SwitchResponseSerializer, ApartmentAddressDefaultQuery


class DeviceAuth(TypedDict):
    username: str
    password: str
    clientid: str


class DeviceView(viewsets.ModelViewSet):
    queryset = Device.objects.order_by('id')
    serializer_class = DeviceSerializer
    permission_classes = [OnlyOperatorOrAdmin, IsAuthenticated]
    http_method_names = ['get', 'post', 'patch']


class DefinitionView(viewsets.ModelViewSet):
    queryset = Definition.objects \
        .order_by('id') \
        .values(
            'address', 'port', 'id',
            'device__name', 'device__number',
            'device__id'
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
        set_ws_status(int(pa), action == "on")
        return Response(self.get_serializer().data)


@csrf_exempt
async def handler_auth(request: http.HttpRequest) -> http.HttpResponse:
    data = cast(DeviceAuth, request.POST.dict())
    device = await Device.hash_check(data['username'], data['password'])
    if device is None:
        await LogDevice.aeasy_create('auth_device', {'username': data['username'], 'access': False})
        return http.HttpResponseForbidden()
    device.delete_at = None
    device.isnot_online = False
    await device.asave(update_fields=('delete_at', 'isnot_online'))
    await LogDevice.aeasy_create('auth_device', {'username': data['username'], 'access': True})
    return http.HttpResponse()


@csrf_exempt
async def handler_event(request: http.HttpRequest) -> http.HttpResponse:
    data = loads(request.body)
    action = data['action']
    await LogDevice.objects.acreate(action=action, payload=data)
    return http.HttpResponse()


class ApartmentAutocomplate(Select2QuerySetView):

    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Address.objects.none()
        forward = self.request.GET.get('forward', '{}')
        data = loads(forward)
        match data:
            case {'address': pa}:
                pass
            case {'static_address': pa}:
                pass
            case _:
                return Address.objects.none()
        queryset = DefinitionAddress.objects \
            .filter(definitions__isnull=True, parent_id=pa)
        if self.q:
            queryset = queryset \
                .annotate(distance=TrigramDistance('apartment', self.q)) \
                .order_by('distance')
        return queryset


@extend_schema(
    summary="Автоматическое заполнение квартир/помещений",
    parameters=[ApartmentAddressDefaultQuery]
)
class ApartmentAddressDefaultView(ListAPIView):
    queryset = DefinitionAddress.objects \
        .filter(definitions__isnull=True, parent_id__isnull=False)
    serializer_class = AddressSerializeList
    lookup_field = "pa"
    pagination_class = None
    permission_classes = [IsAuthenticated, OnlyOperatorOrAdmin]

    def get_queryset(self) -> QuerySet:
        pa = self.request.GET.get('pa', None)
        if pa is None:
            return self.queryset.none()
        return self.queryset.filter(parent_id=pa)[:8]


class Pdf(APIView):
    permission_classes = [IsAuthenticated, OnlyOperatorOrAdmin]

    @staticmethod
    @async_to_sync()
    async def _gen_pdf(devices: Iterable[Device]) -> bytes:
        semaphore = asyncio.Semaphore(5)

        async def __xml_wrapper(device: Device) -> str:
            async with semaphore:
                return await device.xml()

        async with async_playwright() as pw:
            context = await pw.chromium.launch()
            async with context:
                page = await context.new_page()
                async with page:
                    html = ''.join([await __xml_wrapper(_) for _ in devices])
                    await page.set_content(html)
                    content = await page.pdf(format='A4', margin={
                        "top": "20mm",
                        "bottom": "20mm",
                        "left": "15mm",
                        "right": "15mm"
                    })
                    return content

    @staticmethod
    def _to_response(content: bytes) -> http.HttpResponse:
        name = b64encode(token_bytes(6)).decode()
        response = http.HttpResponse(content, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{name}.pdf"'
        return response


    def get(self, request: http.HttpRequest, key: str | None = None):
        queryset = Device.objects.filter(isnot_online__isnull=True)
        if key is not None:
            queryset = queryset.filter(uuid=key)
        results = [*queryset]
        if not results:
            return redirect(request.META.get('HTTP_REFERER', '/'))
        content = self._gen_pdf(results)
        return self._to_response(content)

