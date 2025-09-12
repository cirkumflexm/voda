
from rest_framework.routers import DefaultRouter

from django.urls import path, include

from .views import DeviceView, DefinitionView, Switch

router_private = DefaultRouter()
router_private.register('devices', DeviceView)
router_private.register('definition', DefinitionView)

urlpatterns = [
    path('', include(router_private.urls)),
    path('switch/', Switch.as_view(), name="switch"),
]