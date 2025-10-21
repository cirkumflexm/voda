from django.contrib import admin

from account.models import User


class UserAdmin(admin.ModelAdmin):
    search_fields = ['address__join', 'phone']

    list_display = ['address_id', 'phone', 'address__join']
    ordering = ['id']

admin.site.register(User, UserAdmin)