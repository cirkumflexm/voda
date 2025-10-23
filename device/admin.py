from django.contrib import admin

from device.models import Definition, Device


class DefinitionAdmin(admin.ModelAdmin):
    search_fields = ['address__join']

    list_display = ['id', 'address__join', 'number', 'device__name']
    ordering = ['id']

admin.site.register(Definition, DefinitionAdmin)
admin.site.register(Device)