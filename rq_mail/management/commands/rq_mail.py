from __future__ import absolute_import

from django.core.management.base import BaseCommand

from redis.exceptions import ConnectionError

from rq_mail.dispatcher import Dispatcher
from rq_mail.queue import get_waiting_queues, get_main_queue
from rq_mail import settings

from rq_mail.backends import get_connection


class Command(BaseCommand):
    def handle(self, *args, **options):
        try:
            connection = get_connection()

            d = Dispatcher([get_main_queue(), ] + get_waiting_queues(settings.FALLBACK_STEPS),
                           max_errors=len(settings.FALLBACK_STEPS),
                           connection=connection)

            d.dispatch()
        except ConnectionError as e:
            print(e)
