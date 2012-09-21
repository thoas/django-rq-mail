import time
import traceback

from rq.worker import Worker, green, blue, StopRequested
from rq.exceptions import UnpickleError

from rq_mail.queue import WaitingQueue


class Dispatcher(Worker):
    def __init__(self, *args, **kwargs):
        self.max_errors = kwargs.pop('max_errors')

        super(Dispatcher, self).__init__(*args, **kwargs)

    def dispatch(self, burst=False):  # noqa
        self._install_signal_handlers()

        did_perform_work = False
        self.register_birth()
        self.log.info('RQ dispatcher started')
        self.state = 'starting'
        qnames = self.queue_names()
        self.procline('Listening on %s' % ','.join(qnames))
        self.log.info('')
        self.log.info('*** Listening on %s...' %
                      green(', '.join(qnames)))
        try:
            while True:
                if self.stopped:
                    self.log.info('Stopping on request.')
                    break
                self.state = 'idle'
                wait_for_job = not burst

                try:
                    result = WaitingQueue.dequeue_any(self.queues, wait_for_job,
                                                      connection=self.connection)
                except StopRequested:
                    break
                except UnpickleError as e:
                    msg = '*** Ignoring unpickleable data on %s.' % green(e.queue.name)
                    self.log.warning(msg)
                    self.log.debug('Data follows:')
                    self.log.debug(e.raw_data)
                    self.log.debug('End of unreadable data.')

                    self.failed_queue.push_job_id(e.job_id)
                    continue
                else:
                    for job, queue in result:
                        self.state = 'busy'

                        self.log.info('%s: %s (%s)' % (green(queue.name),
                                                       blue(job.description), job.id))

                        self.fork_and_perform_job(job)

                        did_perform_work = True

                    time.sleep(1)
        finally:
            if not self.is_horse:
                self.register_death()
        return did_perform_work

    def move_to_failed_queue(self, job, *exc_info):
        job_error_key = job.get_id() + ':error'

        errors_counter = self.connection.get(job_error_key)

        exc_string = ''.join(traceback.format_exception(*exc_info))

        if errors_counter and int(errors_counter) > self.max_errors - 1:
            self.log.warning('Moving job to %s queue.' % self.failed_queue.name)
            return self.failed_queue.quarantine(job, exc_info=exc_string)

        if not errors_counter:
            errors_counter = 0
        else:
            errors_counter = int(errors_counter)

        errors_counter += 1

        self.connection.set(job_error_key, errors_counter)

        waiting_queue = self.queues[errors_counter]

        self.log.warning('Moving job to %s queue.' % waiting_queue.name)

        waiting_queue.quarantine(job,
                                 exc_info=exc_string,
                                 timestamp=time.time() + waiting_queue.step)
