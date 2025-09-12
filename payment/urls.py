from django.urls import path

from .views import *


urlpatterns = [
    path('create/', Create.as_view()),
    path('tariff/', CreateForTestTariff.as_view()),
    path('check/', Check.as_view()),
]