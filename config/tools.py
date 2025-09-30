import logging

from django.http import JsonResponse
from rest_framework import serializers
from functools import wraps

from rest_framework.response import Response


class Pa:
    pa = serializers.CharField(label="Лицевой счет")


class GetPa:
    pa = serializers.SerializerMethodField(label="Лицевой счет")

    @staticmethod
    def get_pa(model) -> str:
        return f'{model.pa:0>12}' if getattr(model, 'pa', False) else ''


def assertion_response(func):
    @wraps(func)
    def wrapper(request, *args, **kwargs):
        try:
            return func(request, *args, **kwargs)
        except AssertionError as ex:
            logging.warning(ex)
            return Response(str(ex), status=400)

    return wrapper