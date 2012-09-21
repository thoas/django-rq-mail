from django.conf import settings

PREFIX = getattr(settings, 'RQ_MAIL_PREFIX', 'rq_mail:')

DEFAULT_QUEUE = getattr(settings, 'RQ_MAIL_DEFAULT_QUEUE', 'default')

EMAIL_BACKEND = getattr(settings, 'RQ_MAIL_EMAIL_BACKEND', 'django.core.mail.backends.smtp.EmailBackend')

REDIS_HOST = getattr(settings, 'RQ_MAIL_REDIS_HOST', 'localhost')
REDIS_PORT = getattr(settings, 'RQ_MAIL_REDIS_PORT', 6379)
REDIS_PASSWORD = getattr(settings, 'RQ_MAIL_REDIS_PASSWORD', None)
REDIS_DB = getattr(settings, 'RQ_MAIL_REDIS_DB', 0)

FALLBACK_STEPS = getattr(settings, 'RQ_MAIL_FALLBACK_STEPS', [
    300,
    900,
    1800,
    3600
])
