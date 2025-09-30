from django.http import JsonResponse
from rest_framework.request import Request


class WrapResponseMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: Request):
        response = self.get_response(request)
        if '/' == request.path or \
            '/schema/' in request.path or \
            '/admin/' in request.path:
            return response
        return JsonResponse({
            'status': 'success' if response.reason_phrase == "OK" else "error",
            'data': getattr(response, "data", None)
        }, status=response.status_code)

