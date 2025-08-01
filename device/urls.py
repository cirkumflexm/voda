
from rest_framework.routers import DefaultRouter

from django.urls import path, include

from .views import DeviceView, EncoardView


router_private = DefaultRouter()
router_private.register('devices', DeviceView)
router_private.register('encoders', EncoardView)

urlpatterns = [
    path('', include(router_private.urls))
]