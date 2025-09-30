
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from account.views import *

router_private = DefaultRouter()
router_private.register('users', UserView)

urlpatterns = [
    path('token/refresh/', Refresh.as_view(), name='token_refresh'),
    path('login/', LoginAPIView.as_view(), name="login"),
    path('login/operator/', LoginOperator.as_view(), name="login-operator"),
    path('next/done/', NextDoneView.as_view(), name="next-done"),
    path('logout/', LogoutAPIView.as_view(), name="logout"),
    path('next/', RegistrationView.as_view(), name="next"),
    path('', include(router_private.urls), name='users'),
    path('info/<slug:pa>', DataView.as_view(), name='info'),
    path('my/', MyUserView.as_view(), name='my'),
    path('login/submit/', DoubleAuthentication.as_view(), name='login_submit'),
    path('next/submit/', DoubleRegistration.as_view(), name='registration_submit'),
    path('temp-test/__get_sms_list__', TempGetCodesList.as_view()),
    path('temp-test/__fast_auth_user__', FastAuthUser.as_view()),
]
