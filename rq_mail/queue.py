import times
import time

try:
    from logbook import Logger
except ImportError:
    from logging import Logger # NOQA

from rq import Queue
from rq.job import Job, Status
from rq.exceptions import UnpickleError, NoSuchJobError
from rq.connections import resolve_connection

from rq_mail import settings

logger = Logger(__name__)


def add_prefix(name):
    return settings.PREFIX + name


def get_waiting_queues(steps, connection=None):
    """Returns a handle to the special waiting queue."""
    return [WaitingQueue(name=add_prefix('waiting:%s' % step),
                         connection=connection,
                         step=step)
            for step in steps]


def get_main_queue(connection=None):
    return WaitingQueue(name=add_prefix(settings.DEFAULT_QUEUE), connection=connection)


def enqueue(func, *args, **kwargs):
    get_main_queue(connection=kwargs.pop('connection', None)).enqueue(func, *args, **kwargs)


class WaitingQueue(Queue):
    def __init__(self, name='waiting', step=0, *args, **kwargs):

        self._default_timestamp = kwargs.pop('default_timestamp', 0.0)

        self.step = step

        super(WaitingQueue, self).__init__(name, *args, **kwargs)

    def enqueue(self, f, *args, **kwargs):
        """Creates a job to represent the delayed function call and enqueues
        it.

        Expects the function to call, along with the arguments and keyword
        arguments.

        The function argument `f` may be any of the following:

        * A reference to a function
        * A reference to an object's instance method
        * A string, representing the location of a function (must be
          meaningful to the import context of the workers)
        """
        if not isinstance(f, basestring) and f.__module__ == '__main__':
            raise ValueError(
                'Functions from the __main__ module cannot be processed '
                'by workers.')

        # Detect explicit invocations, i.e. of the form:
        #     q.enqueue(foo, args=(1, 2), kwargs={'a': 1}, timeout=30)
        timeout = None
        result_ttl = None
        timestamp = None
        if 'args' in kwargs or 'kwargs' in kwargs:
            assert args == (), 'Extra positional arguments cannot be used when using explicit args and kwargs.'  # noqa
            timeout = kwargs.pop('timeout', None)
            timestamp = kwargs.pop('timestamp', None)
            args = kwargs.pop('args', None)
            result_ttl = kwargs.pop('result_ttl', None)
            kwargs = kwargs.pop('kwargs', None)

        return self.enqueue_call(func=f, args=args, kwargs=kwargs,
                                 timeout=timeout, result_ttl=result_ttl, timestamp=timestamp)

    def enqueue_call(self, func, args=None, kwargs=None, timeout=None,
                     result_ttl=None, timestamp=None):
        """Creates a job to represent the delayed function call and enqueues
        it.

        It is much like `.enqueue()`, except that it takes the function's args
        and kwargs as explicit arguments.  Any kwargs passed to this function
        contain options for RQ itself.
        """
        timeout = timeout or self._default_timeout
        job = Job.create(func, args, kwargs, connection=self.connection,
                         result_ttl=result_ttl, status=Status.QUEUED)
        return self.enqueue_job(job, timeout=timeout, timestamp=timestamp)

    def enqueue_job(self, job, timeout=None, set_meta_data=True, timestamp=None):
        """Enqueues a job for delayed execution.

        When the `timeout` argument is sent, it will overrides the default
        timeout value of 180 seconds.  `timeout` may either be a string or
        integer.

        If the `set_meta_data` argument is `True` (default), it will update
        the properties `origin` and `enqueued_at`.

        If Queue is instantiated with async=False, job is executed immediately.
        """
        if set_meta_data:
            job.origin = self.name
            job.enqueued_at = times.now()

        if timeout:
            job.timeout = timeout  # _timeout_in_seconds(timeout)
        else:
            job.timeout = 180  # default

        if not timestamp:
            timestamp = self._default_timestamp

        if self._async:
            job.save()
            self.push_job_id(job.id, timestamp)
        else:
            job.perform()
            job.save()
        return job

    def push_job_id(self, job_id, timestamp):
        self.connection.zadd(self.key, job_id, timestamp)

    @classmethod
    def lpop(cls, queue_keys, blocking, connection=None):
        """Helper method.  Intermediate method to abstract away from some
        Redis API details, where LPOP accepts only a single key, whereas BLPOP
        accepts multiple.  So if we want the non-blocking LPOP, we need to
        iterate over all queues, do individual LPOPs, and return the result.

        Until Redis receives a specific method for this, we'll have to wrap it
        this way.
        """
        connection = resolve_connection(connection)

        timestamp = int(time.time())

        for queue_key in queue_keys:
            values = connection.zrevrangebyscore(queue_key, timestamp, 0)

            if values:
                connection.zremrangebyscore(queue_key, 0, timestamp)

                yield queue_key, values

    @classmethod
    def dequeue_any(cls, queues, blocking, connection=None):
        """Class method returning the Job instance at the front of the given
        set of Queues, where the order of the queues is important.

        When all of the Queues are empty, depending on the `blocking` argument,
        either blocks execution of this function until new messages arrive on
        any of the queues, or returns None.
        """
        queue_keys = [q.key for q in queues]

        for queue_key, job_ids in cls.lpop(queue_keys, blocking, connection=connection):

            for job_id in job_ids:
                queue = cls.from_queue_key(queue_key, connection=connection)

                try:
                    job = Job.fetch(job_id, connection=connection)
                except NoSuchJobError:
                    pass
                except UnpickleError as e:
                    # Attach queue information on the exception for improved error
                    # reporting
                    e.job_id = job_id
                    e.queue = queue
                    raise e
                else:
                    yield job, queue

    def quarantine(self, job, exc_info, **kwargs):
        """Puts the given Job in quarantine (i.e. put it on the failed
        queue).

        This is different from normal job enqueueing, since certain meta data
        must not be overridden (e.g. `origin` or `enqueued_at`) and other meta
        data must be inserted (`ended_at` and `exc_info`).
        """
        job.ended_at = times.now()
        job.exc_info = exc_info
        return self.enqueue_job(job, timeout=job.timeout, set_meta_data=False, **kwargs)
