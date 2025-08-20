
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import AddressView


# route = DefaultRouter()
# route.register('addresses', AddressView)


urlpatterns = [
    # path('', include(route.urls), name='addresses')
    path('list/', AddressView.as_view({'get': 'list'}), name='address_list'),
    path('list/<str:personal_account>/', AddressView.as_view({'get': 'retrieve'}), name='address_retrieve'),
]