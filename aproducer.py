# aproducer.py
#
# Async Producer-consumer problem.
# Challenge: How to implement the same functionality, but no threads.

import time
from collections import deque
import heapq


class Scheduler:
    def __init__(self):
        self.ready = deque()     # Functions ready to execute
        self.sleeping = []       # Sleeping functions
        self.sequence = 0

    def call_soon(self, func):
        self.ready.append(func)

    def call_later(self, delay, func):
        self.sequence += 1
        deadline = time.time() + delay     # Expiration time
        # Priority queue
        heapq.heappush(self.sleeping, (deadline, self.sequence, func))

    def run(self):
        while self.ready or self.sleeping:
            if not self.ready:
                # Find the nearest deadline
                deadline, _, func = heapq.heappop(self.sleeping)
                difference = deadline - time.time()
                if difference > 0:
                    time.sleep(difference)
                self.ready.append(func)

            while self.ready:
                func = self.ready.popleft()
                func()


sched = Scheduler()     # Behind scenes scheduler object


"""
    Scheduler - Решает какие функции нужно вызвать сразу, а какие вызвать позже в определенное время

    call_soon - Добавляет функцию в очередь готовых к выполнению

    call_later - Добавляет в очередь ждущих выполнения функцию вместе с временем ее вызова в будущем

    run - Запускает выполнение функций

    Запускает цикл, который выполняется пока в очереди готовых или ждущих что то есть

        Если в очереди готовых ничего нет:

            То из очереди ждущих, достает функцию, у которой самое ближайшее время вызова

            Вычисляет оставшееся до вызова время

            Если оно больше нуля, то делает паузу на это время, а после добавляет в очередь готовых

            Если оно равно или меньше нуля, то сразу добавляет в очередь готовых

        А после достает все функции из очереди готовых и вызывает

        Если в очереди готовых что то есть, то сразу достает все функции из очереди готовых и вызывает

        Цикл начинает новую итерацию

    Простыми словами метод run:
    Достает все фукнции из очереди готовых и вызывает их
    Если в очереди готовых ничего нет, то достает ближайщую функцию из очереди ждущих,
    добавляет в очередь готовых, достает оттуда и вызывает

"""

# ==========================================================================================


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
