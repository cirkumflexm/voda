
from random import randint
from typing import Any

from django import forms
from django.contrib.auth.hashers import make_password
from django.utils.crypto import get_random_string
from django.core.mail import send_mail
from django.utils.text import slugify
from transliterate import translit

from config.settings.email import DEFAULT_FROM_EMAIL
from account.models import Operator


class AddOperatorAdminForm(forms.ModelForm):

    last_name = forms.CharField(
        label='Фамилия',
        required=True
    )
    first_name = forms.CharField(
        label='Имя',
        required=True
    )
    patronymic = forms.CharField(
        label='Отчество',
        required=False
    )
    email = forms.EmailField(
        label='Email',
        required=True
    )

    class Meta:
        model = Operator
        fields = ('fio',)

    def save(self, commit: bool = True) -> Any:
        data = self.cleaned_data
        fio = (data['last_name'], data['first_name'], data['patronymic'])
        fio = ' '.join(str(_) for _ in fio if _)
        self.instance.fio = fio
        self.instance.is_staff = True
        username = f'{data['last_name']}{data['first_name']}{randint(1, 100)}'
        username = translit(username, language_code='ru', reversed=True)
        self.instance.username = slugify(username)
        self.instance.email = data['email']
        password = get_random_string(8)
        self.instance.password = make_password(password)
        send_mail(
            subject="Ваш пароль zesu!",
            message=f'Ваш пароль: {password}',
            from_email=DEFAULT_FROM_EMAIL,
            recipient_list=[data['email']]
        )
        return super().save(commit)
