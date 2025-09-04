from rest_framework import serializers


class Pa:
    pa = serializers.CharField(label="Лицевой счет")


class GetPa:
    pa = serializers.SerializerMethodField(label="Лицевой счет")

    @staticmethod
    def get_pa(model) -> str:
        return f'{model.pa:0>12}' if getattr(model, 'pa', False) else ''
