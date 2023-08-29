import time
from collections import deque
import heapq
# from scheduler import Scheduler


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
            # Drive as a generator
            try:
                self.current.send(None)   # Send to a coroutine
                if self.current:
                    self.ready.append(self.current)
            except StopIteration:
                pass


sched = Scheduler() 


class AsyncQueue:
    def __init__(self):
        self.items = deque()
        self.waiting = deque()

    async def put(self, item):
        self.items.append(item)
        if self.waiting:
            sched.ready.append(self.waiting.popleft())

    async def get(self):
        if not self.items:
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
    await q.put(None)   # "Sentinel" to shut down


async def consumer(q):
    while True:
        item = await q.get()
        if item is None:
            break
        print('Consuming', item)

    print('Consumer done')


sched.new_task(producer(aq, 10))
sched.new_task(consumer(aq))
sched.run()


"""
    AsyncQueue решает проблему блокировки потока выполнения при ожидании данных из очереди. Вместо того, чтобы ждать
    в цикле или использовать семафоры или условные переменные, AsyncQueue позволяет продолжить выполнение других задач до
    тех пор, пока данные не станут доступны.

    AsyncQueue решает проблему опустошения очереди, но не решает проблему ее переполнения
    Она лишь кладет элементы в очередь, не проверяя, полна ли она, и оповещает ждущий геттер, если он есть


    put - Кладет данные в очередь, не проверяя ее заполненность
    Если есть ждущий потребитель, оповщает его о появлении данных

    Более подробно:
    Вставляет данные в очередь
    Если в очереди ожидающих потребителей есть что то, берет первый и отдает его планировщику в очередь готовых к вызову


    get - Если в очереди есть данные, отдает их
    Если нет, начинает ждать их появления и отдает контроль управления

    Более подробно:
    Вызывает функцию потребитель передавая ей первый елемент из очереди
    Если очередь елементов пуста, вставляет в очередь ожидающих геттеров себя же, вместе с переданным ему в аргументы
    потребителем.

    Идея заключается в том, что при отсутствии данных, вызов потребителя откладывается на более поздний
    момент, когда производитель положит данные в очередь.
"""
