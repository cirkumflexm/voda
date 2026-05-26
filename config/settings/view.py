
from datetime import timedelta


REST_FRAMEWORK = {
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.LimitOffsetPagination',
    'DEFAULT_LIMIT': 30,
    'MAX_LIMIT': 150
}

SIMPLE_JWT = {
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=15),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'CACHE_TYPES': ('rest_framework_simplejwt.token_blacklist.cache.CacheBackend',),
}

SPECTACULAR_SETTINGS = {
    "TITLE": "ВСЕ API",
    "VERSION": "0.0.1",
    "SERVE_INCLUDE_SCHEMA": False,
    "SWAGGER_UI_SETTINGS": {},
    "COMPONENT_SPLIT_REQUEST": True,
    "EXCLUDE_PATHS": [
        r"^/source/"
    ]
}

ADMIN_REORDER = (
    'sites',
    {'app': 'account', 'label': 'Аккаунты', 'models': ('account.User',)},
    {'app': 'address', 'label': 'Адреса', 'models': ('address.Address', 'address.IncompleteAddress')},
    {'app': 'device', 'label': 'Устройства', 'models': ('device.Device', 'device.DeleteDevice', 'device.LogDevice')},
    {'app': 'payment', 'label': 'Платежи', 'models': ('payment.Payment',)},
    {'app': 'promo', 'label': 'Промокоды', 'models': ('promo.Promo', 'promo.PromoActivation')},
)
