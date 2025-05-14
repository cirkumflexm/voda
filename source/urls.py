

from rest_framework.routers import DefaultRouter

from django.urls import path, include

from .views import *


router = DefaultRouter()
router.register('users', UserView)
router.register('tariffs', TariffPlanView)

urlpatterns = [
    path('', include(router.urls))
]