from __future__ import absolute_import

from django.core.management.base import BaseCommand

from redis.exceptions import ConnectionError

from rq_mail.dispatcher import Dispatcher
from rq_mail.queue import get_waiting_queues, get_main_queue
from rq_mail import settings

from rq.scripts import setup_redis


class Command(BaseCommand):
    def handle(self, *args, **options):
        try:
            setup_redis(type('lamdbaobject', (object,), {
                'host': settings.REDIS_HOST,
                'port': settings.REDIS_PORT,
                'db': settings.REDIS_DB,
                'password': settings.REDIS_PASSWORD,
                'url': None
            })())

            d = Dispatcher([get_main_queue(), ] + get_waiting_queues(settings.FALLBACK_STEPS),
                           max_errors=len(settings.FALLBACK_STEPS))

            d.dispatch()
        except ConnectionError as e:
            print(e)
