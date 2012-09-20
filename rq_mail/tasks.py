import time
from datetime import datetime

from django.core.mail import get_connection

from rq_mail import settings
from rq_mail.queue import get_waiting_queue, queue_manager

from rq import get_failed_queue


def manage_message(message, *args, **kwargs):
    message.connection = get_connection(settings.EMAIL_BACKEND, fail_silently=False)

    try:
        message.send(fail_silently=False)
        raise Exception('test')
    except Exception, e:
        message.connection = None

        if not hasattr(message, 'errors'):
            message.errors = []

        message.errors.append('[%s] %s: %s' % (datetime.now(), e.__class__.__name__, e))

        if len(message.errors) >= queue_manager.max_errors:
            error_message = '%s times, will not retry.' % len(message.errors)

            failed_queue = get_failed_queue(connection=queue_manager.connection)
            failed_queue.enqueue(manage_message,
                                 message)

        else:
            level = len(message.errors)

            error_message = '%s times, will retry %s times!' % (len(message.errors),
                                                                queue_manager.max_errors - level)

            if level > queue_manager.max_errors - 1:
                level = queue_manager.max_errors - 1

            waiting_queue = get_waiting_queue(connection=queue_manager.connection)
            waiting_queue.enqueue(manage_message,
                                  args=(message,),
                                  timestamp=int(time.time()) + settings.FALLBACK_STEPS[level])

        queue_manager.logger.error('[%s] Email (%s) cannot be send [%s] to %s: %s' % (
            datetime.now(),
            error_message,
            message.subject,
            message.to,
            e
        ))
    else:
        queue_manager.logger.info('[%s] Trying to send the email %s to %s in %s tries' % (
            datetime.now(),
            message.subject,
            message.to,
            1 + len(message.errors) if hasattr(message, 'errors') else 1,
        ))
