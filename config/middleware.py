from django.http import JsonResponse, Http404
from rest_framework.request import Request
from django.urls import resolve


class WrapResponseMiddleware:
    acl = (
        'admin',
        'schema',
        'docs',
        'device:address_autocomplate',
        'device:pdf-download',
        'device:pdf-download-all',
    )

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: Request):
        response = self.get_response(request)
        resolve_data = resolve(request.path_info)
        if any(_ in resolve_data.view_name for _ in self.acl):
            return response
        else:
            return JsonResponse({
                'status': 'success' if response.reason_phrase == "OK" else "error",
                'data': getattr(response, "data", None)
            }, status=response.status_code)


class HandlerAccessMiddleware:
    def __init__(self, get_response) -> None:
        self.get_response = get_response

    def __call__(self, request: Request):
        resolve_data = resolve(request.path_info)
        if resolve_data.view_name in ('handler-auth', 'handler-event'):
            if request.META.get('REMOTE_ADDR') != '127.0.0.1':
                return Http404()
        response = self.get_response(request)
        return response


