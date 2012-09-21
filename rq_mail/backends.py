from django.core.mail.backends.base import BaseEmailBackend
from django.utils.functional import memoize

from rq_mail.queue import enqueue
from rq_mail import settings

from rq.scripts import setup_redis
from rq.connections import get_current_connection
from rq_mail.tasks import manage_message


def _get_connection():
    setup_redis(type('lamdbaobject', (object,), {
        'host': settings.REDIS_HOST,
        'port': settings.REDIS_PORT,
        'db': settings.REDIS_DB,
    })())

    return get_current_connection()


class RqBackend(BaseEmailBackend):
    def send_messages(self, email_messages):

        for message in email_messages:
            enqueue(manage_message, message, connection=get_connection())

        return len(email_messages)

get_connection = memoize(_get_connection, {}, 0)
