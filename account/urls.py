
from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenBlacklistView, TokenRefreshView

from account.views import (
    DataView,
    DoubleAuthentication,
    DoubleRegistration,
    FastAuthUser,
    LoginAPIView,
    MyUserView,
    NextDoneView,
    RegistrationView,
    TempGetCodesList,
    UserView,
)

router_private = DefaultRouter()
router_private.register('users', UserView)

urlpatterns = [
    path('login/', LoginAPIView.as_view(), name="login"),
    path('login/submit/', DoubleAuthentication.as_view(), name='login_submit'),
    path('login/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('login/logout/', TokenBlacklistView.as_view(), name="logout"),
    path('next/', RegistrationView.as_view(), name="next"),
    path('next/submit/', DoubleRegistration.as_view(), name='registration_submit'),
    path('next/done/', NextDoneView.as_view(), name="next-done"),
    path('info/<slug:pa>', DataView.as_view(), name='info'),
    path('my/', MyUserView.as_view(), name='my'),
    path('temp-test/__get_sms_list__', TempGetCodesList.as_view()),
    path('temp-test/__fast_auth_user__', FastAuthUser.as_view()),
    path('', include(router_private.urls), name='users'),
]
