==============
django-rq-mail
==============

django-rq-mail is a simple Python library based on rq_ to store email sent
by Django_ and process them in the background with workers.

As django-rq-queue is based on rq_, it's entirely backed by Redis_.

Architecture
------------

django-rq-mail is not entirely based on rq_ and add new elements to enjoy
features from Redis_ like `Sorted Sets <http://redis.io/commands#sorted_set>`_.

For the purpose of django-rq-queue, it implements the concept of `WaitingQueue`
which delays the processing of a job with a timestamp.

The default behavior of rq_ is to process jobs via `BLPOP` command of redis which
blocks the connection when there are no elements to pop from any of the given queues.
With this behavior there is no way to delays the processing of job and when it's failing
rq_ pushs it in a failed queue.
Of course, you can requeue this job later but there is no fallback mechanism.

In django-rq-mail you can define fallback steps to retry a job until it's not failing anymore
and when a job has been tested on each steps we reintroduce the default behavior of rq_ on pushing
it in the failed queue.


Installation
------------

1. Either check out the package from GitHub_ or it pull from a release via PyPI ::

       pip install django-rq-mail


2. Add 'rq_mail' to your ``INSTALLED_APPS`` ::

       INSTALLED_APPS = (
           'rq_mail',
       )

    to use the `rq_mail` command (via Django commandline) shipped by django-rq-mail.

    This command is a minimal integration of rq_ into Django_ to launch the
    **Dispatcher**.

3. Define ``EMAIL_BACKEND`` ::

       EMAIL_BACKEND = 'rq_mail.backends.RqBackend'

4. Define ``RQ_MAIL_EMAIL_BACKEND`` which is the default behavior to send your emails, for example ::

       RQ_MAIL_EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'


Utilisation
-----------

Configuration
-------------

``RQ_MAIL_PREFIX``
..................

``RQ_MAIL_MAIN_QUEUE``
......................

``RQ_MAIL_EMAIL_BACKEND``
.........................

``RQ_MAIL_REDIS_HOST``
......................

``RQ_MAIL_REDIS_PORT``
......................

``RQ_MAIL_REDIS_DB``
....................

``RQ_MAIL_REDIS_PASSWORD``
..........................

``RQ_MAIL_FALLBACK_STEPS``
..........................

Once you have installed it, you can run `python manage.py rq_mail` from your shell.

.. _Django: https://www.djangoproject.com/
.. _rq: https://github.com/nvie/rq
.. _Redis: http://redis.io/
.. _GitHub: https://github.com/thoas/django-rq-mail
