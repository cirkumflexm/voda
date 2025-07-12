
from django.urls import path

from account.views import *


urlpatterns = [
    path('token/refresh/', Refresh.as_view(), name='token_refresh'),
    path('login/', LoginAPIView.as_view(), name="login"),
    path('logout/', LogoutAPIView.as_view(), name="logout"),
    path('registration/', RegistrationAPIView.as_view(), name="registration"),
]