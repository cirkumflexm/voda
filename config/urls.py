"""
URL configuration for project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin

from django.urls import path, include
from drf_spectacular.views import SpectacularSwaggerView, SpectacularAPIView


urlpatterns = [
    path('admin/', admin.site.urls),
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('', SpectacularSwaggerView.as_view(url_name='schema'), name='docs'),
    path('tariff/', include(('tariff.urls', 'tariff')), name="tariff"),
    path('payment/', include(('payment.urls', 'payment')), name="payment"),
    path('account/', include(('account.urls', 'account')), name="account"),
    path('device/', include(('device.urls', 'device')), name="device"),
    path('address/', include(('address.urls', 'address')), name="address"),
    path('promo/', include(('promo.urls', 'promo')), name="promo"),
]
