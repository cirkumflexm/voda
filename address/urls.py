
from django.urls import path

from .views import AddressView

urlpatterns = [
    path('list/', AddressView.as_view(), name='address_list'),
]
