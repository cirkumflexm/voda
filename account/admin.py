from django.contrib import admin
from phonenumber_field.phonenumber import PhoneNumber

from account.forms import AddOperatorAdminForm
from account.models import Client, Operator


@admin.register(Client)
class UserAdmin(admin.ModelAdmin):
    search_fields = ['address__line', 'phone']
    readonly_fields = ['group']
    fields = (
        'address', 'format_balance', 'definition',
        'tariff_plan', 'format_phone',
        'start_datetime_pp', 'end_datetime_pp',
        'auto_payment', 'is_new',
        'is_verified', 'ws_status'
    )
    list_display = ['username', 'group', 'format_phone', 'address']
    ordering = ['id']

    @admin.display(description="Баланс", ordering='balance')
    def format_balance(self, obj: Client):
        return f'{obj.balance} ₽'

    @admin.display(description="Номер телефона", ordering='phone')
    def format_phone(self, obj: Client) :
        phone = PhoneNumber.from_string(obj.phone, 'ru')
        return phone.as_national

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False


@admin.register(Operator)
class OperatorAdmin(admin.ModelAdmin):
    readonly_fields = ('last_login', 'date_joined', 'group')
    list_display = ['username', 'group', 'fio']
    ordering = ['id']

    def get_form(self, request, obj=None, **kw):
        if obj is None:
            kw['form'] = AddOperatorAdminForm
        return super().get_form(request, obj, **kw)

    def get_fields(self, request, obj=None):
        if obj is None:
            return ('last_name', 'first_name', 'patronymic', 'email')
        return ('last_login', 'date_joined')
