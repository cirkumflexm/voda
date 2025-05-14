from django.http import JsonResponse


class WrapResponseMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if any((
                '/account/' in request.path,
                '/source/' in request.path,
                '/payment/' in request.path,
        )):
            return JsonResponse({
                'status': 'success' if response.reason_phrase == "OK" else "error",
                'data': response.data if hasattr(response, "data") else None
            }, status=response.status_code)
        return response