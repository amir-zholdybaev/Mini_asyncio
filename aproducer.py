# aproducer.py
#
# Async Producer-consumer problem.
# Challenge: How to implement the same functionality, but no threads.

from collections import deque
from scheduler import Scheduler

sched = Scheduler()     # Behind scenes scheduler object


class AsyncQueue:
    def __init__(self):
        self.items = deque()
        self.waiting = deque()    # All getters waiting for data

    def put(self, item):
        self.items.append(item)
        if self.waiting:
            func = self.waiting.popleft()
            # Do we call it right away? No. Schedule it to be called.
            sched.call_soon(func)

    def get(self, callback):
        # Wait until an item is available. Then return it
        if self.items:
            callback(self.items.popleft())
        else:
            self.waiting.append(lambda: self.get(callback))


aq = AsyncQueue()


"""
    pass
"""

# ==========================================================================================


def producer(q, count):
    def _run(n):
        if n < count:
            print('Producing', n)
            q.put(n)
            sched.call_later(1, lambda: _run(n + 1))
        else:
            print('Producer done')
            q.put(None)
    _run(0)


def consumer(q):
    def _consume(item):
        if item is None:
            print('Consumer done')
        else:
            print('Consuming', item)
            sched.call_soon(lambda: consumer(q))
    q.get(callback=_consume)


sched.call_soon(lambda: producer(aq, 10))
sched.call_soon(lambda: consumer(aq,))
sched.run()
