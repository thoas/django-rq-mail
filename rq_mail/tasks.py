from django.core.mail import get_connection

from rq_mail import settings


def manage_message(message, *args, **kwargs):
    message.connection = get_connection(settings.EMAIL_BACKEND,
                                        fail_silently=False)

    try:
        message.send(fail_silently=False)
    except Exception, e:
        message.connection = None
        raise e
