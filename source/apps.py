from django.apps import AppConfig

from django.db.models.signals import post_migrate


def init_data(**kwargs) -> None:
    pass
    # from django.db.models import QuerySet
    # from django.contrib.auth.models import Group

    # if not QuerySet(Group).exists():
# admin = QuerySet(Group).create(name="💠 Администраторы")
# admin.permissions.add(*range(1, 37))
# operator = QuerySet(Group).create(name="⚙️ Оператор")
# operator.permissions.add(36, 32, 28, 25, 24)
# user = QuerySet(Group).create(name="🚀 Пользователи")
# user.permissions.add(36, 32, 28)


class MainConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'source'

    def ready(self):
        post_migrate.connect(init_data, sender=self)


