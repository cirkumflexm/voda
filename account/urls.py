
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from account.views import *

router_private = DefaultRouter()
router_private.register('users', UserView)

urlpatterns = [
    path('token/refresh/', Refresh.as_view(), name='token_refresh'),
    path('login/', LoginAPIView.as_view(), name="login"),
    path('login-operator/', LoginOperator.as_view(), name="login-operator"),
    path('logout/', LogoutAPIView.as_view(), name="logout"),
    path('registration/', RegistrationView.as_view(), name="registration"),
    path('', include(router_private.urls), name='users'),
    path('info/<slug:pa>', DataView.as_view(), name='info'),
    path('code/submit/', DoubleAuthentication.as_view(), name='code_submit'),
    path('temp-test/__get_sms_list__', TempGetCodesList.as_view()),
    path('temp-test/__fast_auth_user__', FastAuthUser.as_view()),
]
