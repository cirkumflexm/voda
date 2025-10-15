from django.urls import path

from .views import *


urlpatterns = [
    path('create/', Create.as_view()),
    path('action/', CreateForTestTariff.as_view()),
    path('onauto/', OnAutoPayment.as_view()),
]