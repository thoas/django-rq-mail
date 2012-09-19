from django.core.mail.backends.base import BaseEmailBackend

from rq_mail.worker import queue_manager


class RqBackend(BaseEmailBackend):
    def send_messages(self, email_messages):
        for message in email_messages:
            queue_manager.add(message)

        return len(email_messages)
