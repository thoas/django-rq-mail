from rq import Queue


class WaitingQueue(Queue):
    def __init__(self, name='waiting', connection=None):
        super(WaitingQueue, self).__init__(name, connection=connection)
