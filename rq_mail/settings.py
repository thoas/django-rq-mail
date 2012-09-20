from django.conf import settings

PREFIX = getattr(settings, 'RQ_MAIL_PREFIX', 'rq_mail:')

DEFAULT_QUEUE = getattr(settings, 'RQ_MAIL_DEFAULT_QUEUE', 'default')

EMAIL_BACKEND = getattr(settings, 'RQ_MAIL_EMAIL_BACKEND', 'django.core.mail.backends.smtp.EmailBackend')

CONNECTION = getattr(settings,
                     'RQ_MAIL_CONNECTION',
                     {'host': 'localhost', 'port': 6379, 'db': 0})

MAX_ERRORS = getattr(settings, 'RQ_MAIL_MAX_ERRORS', 5)

FALLBACK_STEPS = getattr(settings, 'RQ_MAIL_FALLBACK_STEPS', [
    300,
    900,
    1800,
    3600
])
