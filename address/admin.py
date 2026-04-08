from django.contrib import admin

from address.models import IncompleteAddress, Address


class BaseAddressAdmin(admin.ModelAdmin):
    search_fields = ['line']
    list_display = ['line']
    readonly_fields = ['fias', 'city', 'pa']

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(IncompleteAddress)
class IncompleteAddressAdmin(BaseAddressAdmin):
    pass


