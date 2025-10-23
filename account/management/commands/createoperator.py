
from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand, CommandParser
from django.db.models import QuerySet

from account.models import User


class Command(BaseCommand):
    def add_arguments(self, parser: CommandParser):
        parser.add_argument(
            'username',
            type=str
        )
        parser.add_argument(
            'password',
            type=str
        )

    def handle(self, *args, **options):
        username = options['username']
        password = options['password']
        __user = QuerySet(User).create(username=username, password=make_password(password))
        __user.groups.add(2)
        print("Успешно!")