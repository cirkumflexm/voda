from django.urls import path, include

from promo.views import PromoCheckView

urlpatterns = [
    path('check/<slug:promo>', PromoCheckView.as_view(), name='promo_check')
]