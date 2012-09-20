from __future__ import absolute_import

from django.core.management.base import BaseCommand
from django.core.management.base import CommandError

from redis.exceptions import ConnectionError

from rq_mail.dispatcher import Dispatcher
from rq_mail.queue import get_waiting_queue, queue_manager

from rq import Worker


def run_worker(queue_manager):
    w = Worker(queue_manager.queue, connection=queue_manager.connection)
    w.work()


def run_dispatcher(queue_manager):
    connection = queue_manager.connection

    d = Dispatcher(get_waiting_queue(connection=connection),
                   connection=connection)
    d.dispatch()

commands = {
    'worker': run_worker,
    'dispatcher': run_dispatcher
}


class Command(BaseCommand):
    def handle(self, command, *args, **options):
        try:
            if not command in commands:
                raise CommandError('Command %s not found' % command)

            commands[command](queue_manager)
        except ConnectionError as e:
            print(e)
