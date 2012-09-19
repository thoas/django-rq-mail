from django.core.management.base import BaseCommand

from redis.exceptions import ConnectionError

from rq import Worker


class Command(BaseCommand):
    def handle(self, *args, **options):
        from rq_mail.worker import queue_manager

        try:
            w = Worker(queue_manager.queues.values(),
                       connection=queue_manager.connection)
            w.work()
        except ConnectionError as e:
            print(e)
