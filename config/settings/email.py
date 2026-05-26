
from config.settings.env import EMAIL_HOST_USER, EMAIL_HOST_PASSWORD, DEFAULT_FROM_EMAIL

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

EMAIL_HOST = 'smtp.mail.me.com'
EMAIL_PORT = 587
EMAIL_USE_SSL = False
EMAIL_USE_TLS = True

__all__ = (
    'EMAIL_BACKEND', 'EMAIL_HOST', 'EMAIL_PORT',
    'EMAIL_USE_SSL', 'EMAIL_USE_TLS', 'EMAIL_HOST_USER',
    'EMAIL_HOST_PASSWORD', 'DEFAULT_FROM_EMAIL'
)
