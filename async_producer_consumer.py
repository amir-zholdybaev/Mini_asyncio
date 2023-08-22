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
            print('put into waiting')


aq = AsyncQueue()


"""
    put - вставляет елемент в очередь елементов
    Если в очереди ждущих геттеров есть что то, берет первый и отдает планировщику в очередь готовых к вызову

    Более абстрактно:
    Кладет данные в очередь
    Если есть ждущий геттер, оповщает его о появлении данных


    get - Берет первый елемент из очереди елементов и отдает его потребителю, вызывая его
    Если в очереди елементов пусто, вставляет в очередь геттеров себя же, вместе с переданным ему в аргументы потребителем

    Более абстрактно:
    Если в очереди есть данные, отдает их
    Если нет начинает ждать появления данных

    AsyncQueue решает проблему блокировки потока выполнения при ожидании данных из очереди. Вместо того, чтобы ждать
    в цикле или использовать семафоры или условные переменные, AsyncQueue позволяет продолжить выполнение других задач до
    тех пор, пока данные не станут доступны.

    AsyncQueue решает проблему опустошения очереди, но не решает проблему ее переполнения
    Она лишь кладет элементы в очередь, не проверяя, полна ли она, и оповещает ждущий геттер, в случае, если он есть
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
