import time
from collections import deque
import heapq


class Scheduler:
    def __init__(self):
        self.ready = deque()    # Functions ready to execute
        self.sleeping = []  # Sleeping functions
        self.sequence = 0

    def call_soon(self, func):
        self.ready.append(func)

    def call_later(self, delay, func):
        self.sequence += 1
        deadline = time.time() + delay  # Expiration time
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


sched = Scheduler()


def count_down(n):
    if n > 0:
        print('Down', n)
        # time.sleep(4)   # Blocking call (nothing else can run)
        sched.call_later(4, lambda: count_down(n - 1))


def count_up(stop):
    def _run(x):
        if x < stop:
            print('Up', x)
            # time.sleep(1)
            sched.call_later(1, lambda: _run(x + 1))
    _run(0)


sched.call_soon(lambda: count_down(5))
sched.call_soon(lambda: count_up(20))
sched.run()
