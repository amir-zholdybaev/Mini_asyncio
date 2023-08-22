# aproducer.py
#
# Async Producer-consumer problem.
# Challenge: How to implement the same functionality, but no threads.

from collections import deque
from scheduler import Scheduler

sched = Scheduler()     # Behind scenes scheduler object


class QueueClosed(Exception):
    pass


class Result:
    def __init__(self, value=None, exc=None):
        self.value = value
        self.exc = exc

    def result(self):
        if self.exc:
            raise self.exc
        else:
            return self.value


class AsyncQueue:
    def __init__(self):
        self.items = deque()
        self.waiting = deque()    # All getters waiting for data
        self._closed = False    # Can queue be used anymore?

    def close(self):
        self._closed = True
        if self.waiting and not self.items:
            for func in self.waiting:
                sched.call_soon(func)

    def put(self, item):
        if self._closed:
            raise QueueClosed()

        self.items.append(item)
        if self.waiting:
            func = self.waiting.popleft()
            # Do we call it right away? No. Schedule it to be called.
            sched.call_soon(func)

    def get(self, callback):
        # Wait until an item is available. Then return it
        # Question: How does a closed queue interact  with get()
        if self.items:
            callback(Result(value=self.items.popleft()))  # Good result
        else:
            # No items available (must wait)
            if self._closed:
                callback(Result(exc=QueueClosed()))  # Error result
            else:
                self.waiting.append(lambda: self.get(callback))
                print('put into waiting')


aq = AsyncQueue()


def producer(q, count):
    def _run(n):
        if n < count:
            print('Producing', n)
            q.put(n)
            sched.call_later(2, lambda: _run(n + 1))
        else:
            print('Producer done')
            q.close()   # Means no more items will be produced

    _run(0)


def consumer(q):
    def _consume(result):
        try:
            item = result.result()
            print('Consuming', item)
            sched.call_soon(lambda: consumer(q))

        except QueueClosed:
            print('Consumer done')

    q.get(callback=_consume)


sched.call_soon(lambda: producer(aq, 10))
sched.call_soon(lambda: consumer(aq,))
sched.run()

"""
    TODO
    Понять работу кода
    Понять почему if self.waiting and not self.items: все равно работает
    Вынести функции продюсера и консюмера в файл async_producer_consumer_with_error.py
    Понят что автор сказал о классе Result и фьючерсах
"""
