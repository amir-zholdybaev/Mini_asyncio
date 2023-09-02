from collections import deque
from scheduler import Scheduler

sched = Scheduler() 


class Awaitable:
    def __await__(self):
        yield


def switch():
    return Awaitable()


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
    Если в очереди есть данные, отдает их
    Если очередь пуста, вставляет потребителя, из которого был вызван, в очередь потребителей ожидающих данных,
    забирает потребителя у планировщика, тем самым не давая ему вызвать потребителя еще раз, до тех пор, пока в очереди
    данных не появятся новые данные. Отдает контроль управления

    Идея заключается в том, что при отсутствии данных, вызов потребителя откладывается на более поздний
    момент, когда производитель положит данные в очередь.
"""
