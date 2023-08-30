import time
from collections import deque
import heapq


class Scheduler:
    def __init__(self):
        self.ready = deque()     # Functions ready to execute
        self.sleeping = []       # Sleeping functions
        self.sequence = 0
        self.current = None

    def call_soon(self, func):
        self.ready.append(func)

    def call_later(self, delay, func):
        self.sequence += 1
        deadline = time.time() + delay     # Expiration time
        heapq.heappush(self.sleeping, (deadline, self.sequence, func))
        
    def run(self):
        while self.ready or self.sleeping:
            if not self.ready:
                # Find the nearest deadline
                deadline, _, func = heapq.heappop(self.sleeping)
                delta = deadline - time.time()
                if delta > 0:
                    time.sleep(delta)
                self.ready.append(func)

            while self.ready:
                func = self.ready.popleft()
                func()

    # Coroutine-based functions 
    def new_task(self, coro):
        self.ready.append(Task(coro))   # Wrapped coroutine

    async def sleep(self, delay):
        self.call_later(delay, self.current)  
        self.current = None
        await switch()   # Switch to a new task


# Class that wraps a coroutine--making it look like a callback
class Task:
    def __init__(self, coro):
        self.coro = coro        # "Wrapped coroutine"

    def __call__(self):
        try:
            sched.current = self

            self.coro.send(None)
            if sched.current:
                sched.ready.append(self)
        except StopIteration:
            pass


class Awaitable:
    def __await__(self):
        yield


def switch():
    return Awaitable()


sched = Scheduler()    # Background scheduler object


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


# Coroutine-based tasks
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


q = AsyncQueue()
sched.new_task(producer(q, 10))
sched.new_task(consumer(q))


# Call-back based tasks
def countdown(n):
    if n > 0:
        print('Down', n)
        sched.call_later(4, lambda: countdown(n - 1))


def countup(stop):
    def _run(x):
        if x < stop:
            print('Up', x)
            sched.call_later(1, lambda: _run(x + 1))
    _run(0)


sched.call_soon(lambda: countdown(5))
sched.call_soon(lambda: countup(20))
sched.run()


"""
    На самом деле планировщик основан на работе с функциями обратного вызова. Но также адаптирован для работы с
    корутинами(генераторами). Это сделано для того, чтобы с планировщиком можно было работать используя как функции
    обратного вызова так и корутины(генераторы).

    Для того, чтобы корутины могли работать с планировщиком их оборачивают в класс Task, который при вызове, возвращает
    калабл объект, чтобы его можно было вызывать как функцию(через скобки ()).

    Внутри магического метода __call__ написан тот же код вызова готовых корутин, что и в планировщике из файла
    async_await/scheduler.py основанном на ключевых словах async/await:
    1 Обозначение корутины как текущей(sched.current = self)
    2 Вызов корутины(self.coro.send(None))
    3 Помещение текущей корутины в конец очереди готовых, если такая еще есть.
    Весь этот код оборачивается в try/except, с целью отлова исключения StopIteration
    Цикла в методе __call__ нет, так как он реализован снаружи в методе планировщика run().
    В этом цикле как раз и вызывается либо функция обратного вызова либо наш калабл объект

    Также к планировщику основанному на колбэках, для работы с корутинами добавлено 2 метода - new_task и sleep

    new_task - Если мы хотим положить корутину в очередь готовых к вызову, то отдаем ее в метод планировщика new_task,
    который оборачивает корутину в калабл объект класса Task и кладет в очередь.

    sleep - Метод sleep же внутри себя вызывает метод планировщика call_later, передает туда время, через которое корутина
    должна быть вызвана и саму текущую, исполняемую корутину, из которой и был вызван метод sleep. После того, как корутина
    положена в очередь спящих, у нее убирается обозначение как текущей(исполняемой, self.current = None). И в конце концов
    метод sleep отдает контроль управления(await switch())
"""