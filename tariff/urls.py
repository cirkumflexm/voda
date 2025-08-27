from rest_framework.routers import DefaultRouter

from django.urls import path, include

from .views import TariffPlanView, Activate, TariffChoices, ActivationTestTariff

router_private = DefaultRouter()
router_private.register('tariffs', TariffPlanView)
router_private.register('choices', TariffChoices, basename='tariff_choices')

urlpatterns = [
    path('', include(router_private.urls), name='tariffs'),
    path('activate', Activate.as_view(), name='tariff_activate'),
    path('test-tariff', ActivationTestTariff.as_view(), name='activation_test_tariff'),
]