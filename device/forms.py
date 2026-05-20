
from typing import Any
from dal.autocomplete import ModelSelect2

from django import forms
from django.forms.models import ModelFormMetaclass
from django.forms import ModelForm

from device.models import DefinitionAddress, Device


class DeviceFormMeta(ModelFormMetaclass):
    def __new__(cls, name, bases, attrs):
        for num in range(1, 9):
            attrs[f'port_{num}'] = forms.ModelChoiceField(
                queryset=DefinitionAddress.objects.all(),
                widget=ModelSelect2(
                    url='device:address_autocomplate',
                    forward=['address'],
                    attrs={
                        'data-placeholder': '-' * 10,
                    }
                ),
                required=False,
                label=f'Порт №{num} (квартира/помещение)',
            )
        return super().__new__(cls, name, bases, attrs)


class DeviceForm(ModelForm, metaclass=DeviceFormMeta):

    static_address = forms.CharField(widget=forms.HiddenInput(), label='', required=False)

    def __init__(self, *args, instance: Device | None = None, **kw) -> None:
        super().__init__(*args, instance=instance, **kw)
        if instance is not None:
            for key, value in self.fields.items():
                if not key.startswith('port'):
                    continue
                value.widget.forward = ['static_address']
                self.initial[key] = getattr(instance, key)
            self.initial['static_address'] = self.instance.address_id

    def clean(self) -> dict[str, Any] | None:
        cleaned = super().clean()
        if cleaned is None:
            return
        for key, value in cleaned.items():
            if isinstance(value, DefinitionAddress):
                setattr(self.instance, key, value)
        if self.instance and self.instance.pk:
            cleaned['address'] = self.instance.address
        return cleaned

    @property
    def media(self):
        js = ['device/js/check.js']
        if self.instance and self.instance.pk is None:
            js.append('device/js/autocomplate.js')
        media = forms.Media(js=js)
        for field in self.fields.values():
            media += field.widget.media
        return media

    class Meta:
        model = Device
        fields = '__all__'


