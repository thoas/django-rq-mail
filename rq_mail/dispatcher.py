import time

from rq.worker import Worker, green, blue, StopRequested
from rq.exceptions import UnpickleError

from rq_mail.queue import WaitingQueue


class Dispatcher(Worker):
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

                        job, queue = result
                        self.log.info('%s: %s (%s)' % (green(queue.name),
                                                       blue(job.description), job.id))

                        self.fork_and_perform_job(job)

                        did_perform_work = True

                    time.sleep(1)
        finally:
            if not self.is_horse:
                self.register_death()
        return did_perform_work
