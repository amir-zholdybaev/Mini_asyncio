import time
from collections import deque
import heapq
from scheduler import Scheduler

sched = Scheduler() 

class Awaitable:
    def __await__(self):
        yield


def switch():
    return Awaitable()


class QueueClosed(Exception):
    pass


class AsyncQueue:
    def __init__(self):
        self.items = deque()
        self.waiting = deque()
        self._closed = False

    def close(self):
        self._closed = True
        if self.waiting and not self.items:
            sched.ready.append(self.waiting.popleft())  # Reschedule waiting tasks

    async def put(self, item):
        if self._closed:
            raise QueueClosed()

        self.items.append(item)
        if self.waiting:
            sched.ready.append(self.waiting.popleft())

    async def get(self):
        while not self.items:
            if self._closed:
                raise QueueClosed()
            self.waiting.append(sched.current)   # Put myself to sleep
            sched.current = None        # "Disappear"
            await switch()              # Switch to another task

        return self.items.popleft()


aq = AsyncQueue()


async def producer(q, count):
    for n in range(count):
        print('Producing', n)
        await q.put(n)
        await sched.sleep(1)

    print('Producer done')
    q.close()


async def consumer(q):
    try:
        while True:
            item = await q.get()
            print('Consuming', item)
    except QueueClosed:
        print('Consumer done')


sched.new_task(producer(aq, 10))
sched.new_task(consumer(aq))
sched.run()


"""
    Здесь все тоже самое, что и в файле async_queue.py, только теперь в AsyncQueue есть метод close() закрывающий очередь.
    Теперь производителю не нужно класть None в очередь, если ему нужно завершить работу, а просто закрыть очередь.

    Метод get() теперь выбрасывает ошибку QueueClosed, если в очереди нет данных и очередь закрыта. Потребитель должен
    отловить эту ошибку, чтобы корректно завершить свою работу

    Проверка if not self.items: в методе get() заменена на цикл while not self.items:. Это сделано потому что производитель
    теперь не кладет None в очередь, когда хочет завершить работу, а просто закрывает очередь, оставляя ее пустой и геттер
    начиная свое выполнение с места await switch(), не должен дойти до строки return self.items.popleft(). Ведь в таком
    случае произойдет ошибка, так как очередь пуста и там нет даже значения None. Поэтому в случае, если очередь пуста
    и закрыта, то геттер, начиная свое выполениние с места await switch(), должен зайти на новую итерацию цикла, который
    работает в случае пустой очереди, не доходя до строки возвращения результата(return self.items.popleft()). В этой
    новой итерации он проверят не закрыта ли очередь, если закрыта, то выбрасывает исключение QueueClosed, которое
    перехватывает потребитель.
"""