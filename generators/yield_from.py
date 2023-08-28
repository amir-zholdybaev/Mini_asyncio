import time
from collections import deque
import heapq


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
        yield

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
    Все тоже самое, что и в планировщике взаимодействующим с генераторами на операторах yield, только теперь
    вместо операторов yield генераторы используют yield from. Это нужно для того, чтобы два действия -
    вызова метода планировщика(например sched.sleep(4)) и вызова оператора yield(с целью возвращения контроля исполнения),
    можно было умещать в одну строку кода - yield from sched.sleep(4). Однако теперь в конце метода планировщика sleep
    находится оператор yiled. так как yield from работает только с итерируемыми объектами подобно циклу for в оператором
    yield внутри:

    for i in generator:
        yield
"""
