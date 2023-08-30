import time
from collections import deque
import heapq


class Awaitable:
    def __await__(self):
        yield

def switch():
    return Awaitable()

class Scheduler:
    def __init__(self):
        self.ready = deque()
        self.sleeping = [ ] 
        self.current = None    # Currently executing generator
        self.sequence = 0

    async def sleep(self, delay):
        deadline = time.time() + delay
        self.sequence += 1
        heapq.heappush(self.sleeping, (deadline, self.sequence, self.current))
        self.current = None  # "Disappear"
        await switch()       # Switch tasks
        
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

            try:
                self.current.send(None)   # Send to a coroutine
                if self.current:
                    self.ready.append(self.current)
            except StopIteration:
                pass


sched = Scheduler()    # Background scheduler object


async def countdown(n):
    while n > 0:
        print('Down', n)
        await sched.sleep(4)
        n -= 1


async def countup(stop):
    x = 0
    while x < stop:
        print('Up', x)
        await sched.sleep(1)
        x += 1


if __name__ == '__main__':
    sched.new_task(countdown(5))
    sched.new_task(countup(20))
    sched.run()


"""
    Тоже самое, что и в файле generators/yield_from.py, только вместо операторов yield from ключевое слово await
    работает точно также. Еще добавлено ключевое слово async, обозночая генератор корутиной.
"""