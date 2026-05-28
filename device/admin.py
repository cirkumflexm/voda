from json import dumps
from typing import Any

from django.contrib import admin
from django.http import HttpRequest, HttpResponse
from django.urls import reverse
from django.utils.html import format_html

from device.forms import DeviceForm
from device.models import Device, LogDevice


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    autocomplete_fields = ['address']
    list_display = ['status', 'name', 'address', 'delete_via', 'data']
    list_display_links = ['name']
    form = DeviceForm
    actions = None
    ordering = ('-isnot_online',)

    def data(self, device: Device):
        html = '<div style="display:block;text-align:center;">{}</div>'
        if device.isnot_online is None:
            return format_html(
                html, format_html(
                    '<a href="{}">Получить данные</a>',
                    reverse('device:pdf-download', args=(device.uuid,))
                ))
        else:
            return format_html(html, '-')

    def changelist_view(
            self, request: HttpRequest,
            extra_context: dict[str, Any] | None = None
    ) -> HttpResponse:
        type(self).data.short_description = format_html('<a href="{}" style="color:var(--link-fg);text-align:center;">Получить все</a>', reverse('device:pdf-download-all'))
        return super().changelist_view(request, extra_context)

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ('number', 'address')
        return tuple()


@admin.register(LogDevice)
class LogDeviceAdmin(admin.ModelAdmin):
    list_display = ['id', 'action', 'short_payload', 'created_at']
    exclude = ['payload']
    readonly_fields = ['indent_payload']

    @admin.display(description='JSON')
    def short_payload(self, obj: LogDevice):
        return str(obj.payload)[:80] + '...'

    @admin.display(description="JSON")
    def indent_payload(self, obj: LogDevice):
        return format_html('<pre style="white-space: pre-wrap; word-break: break-all; max-width: 800px;">{}</pre>', dumps(obj.payload, indent=4))

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False

