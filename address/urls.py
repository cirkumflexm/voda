
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import AddressView


# route = DefaultRouter()
# route.register('addresses', AddressView)


urlpatterns = [
    # path('', include(route.urls), name='addresses')
    path('list/', AddressView.as_view(), name='address_list')
]