from rest_framework import serializers


class Pa:
    pa = serializers.CharField(label="Лицевой счет")


class GetPa:
    pa = serializers.SerializerMethodField(label="Лицевой счет")

    @staticmethod
    def get_pa(model) -> str:
        return f'{getattr(model, 'pa', ''):0>12}'

