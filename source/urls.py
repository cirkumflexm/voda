

from rest_framework.routers import DefaultRouter

from django.urls import path, include

from .views import UserView, TariffPlanView, DataView


router_private = DefaultRouter()
router_private.register('users', UserView)
router_private.register('tariffs', TariffPlanView)

urlpatterns = [
    path('', include(router_private.urls)),
    path('info/<slug:personal_account>', DataView.as_view()),
]