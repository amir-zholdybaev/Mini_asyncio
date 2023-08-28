import time
from collections import deque
import heapq


def awaitable():
    yield


def switch():
    return awaitable()


class Scheduler:
    def __init__(self):
        self.ready = deque()
        self.sleeping = []
        self.current = None    # Currently executing generator
        self.sequence = 0

    def sleep(self, delay):
        deadline = time.time() + delay
        self.sequence += 1
        heapq.heappush(self.sleeping, (deadline, self.sequence, self.current))
        self.current = None  # "Disappear"
        yield from switch()

    def new_task(self, coro):
        self.ready.append(coro)

    def run(self):
        while self.ready or self.sleeping:
            if not self.ready:
                deadline, _, coro = heapq.heappop(self.sleeping)
                delta = deadline - time.time()
                if delta > 0:
                    time.sleep(delta)
                self.ready.append(coro)

            self.current = self.ready.popleft()
            # Drive as a generator
            try:
                self.current.send(None)   # Send to a coroutine
                if self.current:
                    self.ready.append(self.current)
            except StopIteration:
                pass


sched = Scheduler()    # Background scheduler object


def countdown(n):
    while n > 0:
        print('Down', n)
        yield from sched.sleep(4)
        n -= 1


def countup(stop):
    x = 0
    while x < stop:
        print('Up', x)
        yield from sched.sleep(1)
        x += 1


sched.new_task(countdown(5))
sched.new_task(countup(20))
sched.run()


"""
    Все тоже самое что и в планировщике из файла yield_from.py, только в методе sleep оператор yield заменен на
    yield from switch(). Это нужно для наглядности кода. Метод же switch в свою очередь просто возвращает генератор
    awaitable, в котором прописан только оператор yield. В итоге метод sleep работает точно также как и с оператором
    yield, только теперь на месте этого оператора написана строка yield from switch(), указывая своим названием на
    то, что в этом месте происходит переключение.
"""
