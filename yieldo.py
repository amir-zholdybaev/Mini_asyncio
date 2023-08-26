# yieldo.py
#
# Example of a coroutine-based scheduler

import time
from collections import deque
import heapq

# Plumbing that makes the "await" statement work.  We provide
# a single function "switch" that is used by the schedule to
# switch tasks.


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
        return 100

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

# ---- Example code


def countdown(n):
    while n > 0:
        print('Down', n)
        num = sched.sleep(4)
        yield
        n -= 1


def countup(stop):
    x = 0
    while x < stop:
        print('Up', x)
        sched.sleep(1)
        yield
        x += 1


sched.new_task(countdown(5))
sched.new_task(countup(20))
sched.run()


"""
    Этот способ сделать функции ассинхронными гораздо проще чем колбэки. Тут всего лишь нужно внутри исполняемой функции
    вызвать метод планировщика, который положит эту функцию в очередь ожидающих и вызвать оператор yield, тем самым отдать
    контроль управления из функции. Каким образом метод может положить функцию в очередь ждущих, внутри которой сам
    вызывается?

    Дело в том, что функция сначала скармливается планировщику, который перед ее вызовом кладет ее во внутреннее свойство
    self.current, которое хранит текущую исполняемую функцию. Далее планировщик вызывает эту функцию, внутри нее вызывается
    метод планировщика sleep(), который внутри себя берез функцию из свойства self.current, то есть текущую, из которой
    этот метод был вызван и кладет функцию в очередь ждущих.


    sleep - Добавляет в очередь ждущих выполнения функцию, вместе с временем ее вызова в будущем

    new_task - Добавляет функцию в очередь готовых к выполнению
"""
