from __future__ import absolute_import
from optparse import make_option

from django.core.management.base import BaseCommand

from redis.exceptions import ConnectionError

from rq_mail.dispatcher import Dispatcher
from rq_mail.queue import get_waiting_queues, get_main_queue

from rq_mail import settings

from rq.scripts import setup_redis


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--config',
                    '-c',
                    default=None,
                    help='Module containing RQ settings.'),
        make_option('--host',
                    '-H',
                    default=settings.REDIS_HOST,
                    help='The Redis hostname (default: localhost)'),
        make_option('--port',
                    '-p',
                    default=settings.REDIS_PORT,
                    help='The Redis portnumber (default: 6379)'),
        make_option('--db',
                    '-d',
                    type=int, default=settings.REDIS_DB,
                    help='The Redis database (default: 0)')
    )

    def handle(self, *args, **options):
        try:
            setup_redis(type('lamdbaobject', (object,), options)())

            d = Dispatcher([get_main_queue(), ] + get_waiting_queues(settings.FALLBACK_STEPS),
                           max_errors=len(settings.FALLBACK_STEPS))

            d.dispatch()
        except ConnectionError as e:
            print(e)
