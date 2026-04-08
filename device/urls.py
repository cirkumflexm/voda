
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import DeviceView, DefinitionView, \
        Switch, ApartmentAutocomplate, ApartmentAddressDefaultView, \
        Pdf, handler_auth, handler_event 

router_private = DefaultRouter()
router_private.register('devices', DeviceView)
router_private.register('definition', DefinitionView)

urlpatterns = [
    path('', include(router_private.urls)),
    path('switch/', Switch.as_view(), name="switch"),
    path('autocomplate/', ApartmentAutocomplate.as_view(), name='address_autocomplate'),
    path('default/', ApartmentAddressDefaultView.as_view(), name='address_default'),
    path('download/', Pdf.as_view(), name='pdf-download-all'),
    path('download/<uuid:key>', Pdf.as_view(), name='pdf-download'),
    path('handler/auth/', handler_auth, name='handler-auth'),
    path('handler/event/', handler_event, name='handler-event'),
]
