import logging
import time

from datetime import datetime

from django.core.mail import get_connection

from rq_mail import settings
from rq_mail.queue import WaitingQueue

from redis.client import Redis

from rq import Queue, get_failed_queue

logger = logging.getLogger(__name__)


class QueueManager(object):
    def __init__(self, deltas, default, max_errors, logger, prefix,
                 connection=None, info_key='infos'):
        self.deltas = deltas
        self.max_errors = max_errors
        self.connection = connection

        self.logger = logger
        self.prefix = prefix

        self.default_key = self.add_prefix(default)
        self.info_key = self.add_prefix(info_key)

        self.queues = {}

        self._load_queues()

    def _load_queues(self):

        self.queues['default'] = Queue(name=self.default_key, connection=self.connection)

        now = int(time.time())

        for level in range(self.max_errors - 1):
            l = level + 1

            queue = WaitingQueue(name=self.add_prefix('waiting:%d' % l), connection=self.connection)

            queue.delta = self.deltas[l]

            queue.last_key = 'waiting:%02dmin:last' % queue.delta

            if not self.get_info(queue.last_key):
                self.set_info(queue.last_key, now)

            self.queues[l] = queue

    def set_info(self, key, value, is_incr=False):
        if is_incr:
            self.connection.hincrby(self.info_key, key, value)
        else:
            self.connection.hset(self.info_key, key, value)

    def get_info(self, key):
        return self.connection.hget(self.info_key, key)

    def add(self, message):
        self.queues['default'].enqueue(manage_message, message)

    def add_prefix(self, name):
        return self.prefix + name

queue_manager = QueueManager(deltas=settings.DELTAS,
                             default=settings.DEFAULT_QUEUE,
                             max_errors=settings.MAX_ERRORS,
                             logger=logger,
                             prefix=settings.PREFIX,
                             connection=Redis(**settings.CONNECTION))


def manage_message(message):
    message.connection = get_connection(settings.EMAIL_BACKEND, fail_silently=False)

    try:
        message.send(fail_silently=False)
    except Exception, e:
        message.connection = None

        if not hasattr(message, 'errors'):
            message.errors = []

            queue_manager.set_info('waiting_errors', 1, is_incr=True)

        message.errors.append('[%s] %s: %s' % (datetime.now(), e.__class__.__name__, e))

        if len(message.errors) >= queue_manager.max_errors:
            error_message = '%s times, will not retry.' % len(message.errors)

            queue_manager.set_info('waiting_errors', -1, is_incr=True)

            get_failed_queue(connection=queue_manager.connection).enqueue(manage_message, message)

        else:
            level = len(message.errors)

            error_message = '%s times, will retry %s times!' % (len(message.errors), queue_manager.max_errors - level)

            if level > queue_manager.max_errors - 1:
                level = queue_manager.max_errors - 1

            queue_manager.queues[level].enqueue(manage_message, message)

        queue_manager.logger.error('[%s] Email (%s) cannot be send [%s] to %s: %s' % (
            datetime.now(),
            error_message,
            message.subject,
            message.to,
            e
        ))
    else:
        if hasattr(message, 'errors'):
            queue_manager.set_info('waiting_errors', -1, is_incr=True)

        queue_manager.set_info('sent', 1, is_incr=True)

        queue_manager.logger.info('[%s] Trying to send the email %s to %s in %s tries' % (
            datetime.now(),
            message.subject,
            message.to,
            1 + len(message.errors) if hasattr(message, 'errors') else 1,
        ))
