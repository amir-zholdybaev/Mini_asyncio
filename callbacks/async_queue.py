from collections import deque
from scheduler import Scheduler

sched = Scheduler()     # Behind scenes scheduler object


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
            print('put into waiting')


aq = AsyncQueue()


def producer(q, count):
    def _run(n):
        if n < count:
            print('Producing', n)
            q.put(n)
            sched.call_later(2, lambda: _run(n + 1))
        else:
            print('Producer done')
            q.put(None)

    _run(0)


"""
    Производитель генерирует данные и кладет их в очередь и оповещает потребителя о положенных данных,
    если есть ждущий потребитель
    Делает он это каждые n секунд и до тех пор, пока не достигнет конца счетчика
    Когда счетчик закончен, завершает свою работу
"""


def consumer(q):
    def _consume(item):
        if item is None:
            print('Consumer done')
        else:
            print('Consuming', item)
            sched.call_soon(lambda: consumer(q))

    q.get(callback=_consume)


"""
    Потребитель пытается получить данные
    Если в очереди есть готовые данные, он берет их, обрабатывает и запрашивает по новой (sched.call_soon(lambda: consumer(q)))
    Если в очереди данных нет, он их ждет
    Повторяет он эти действия до тех пор, пока производитель данных не прекратит свою работу
"""

sched.call_soon(lambda: producer(aq, 10))
sched.call_soon(lambda: consumer(aq,))
sched.run()


"""
    AsyncQueue решает проблему блокировки потока выполнения при ожидании данных из очереди. Вместо того, чтобы ждать
    в цикле или использовать семафоры или условные переменные, AsyncQueue позволяет продолжить выполнение других задач до
    тех пор, пока данные не станут доступны.

    AsyncQueue решает проблему опустошения очереди, но не решает проблему ее переполнения
    Она лишь кладет элементы в очередь, не проверяя, полна ли она, и оповещает ждущий геттер, если он есть


    put - Кладет данные в очередь, не проверяя ее заполненность
    Если есть ждущий геттер, оповщает его о появлении данных

    Более подробно:
    Вставляет данные в очередь
    Если в очереди ожидающих геттеров есть что то, берет первый и отдает его планировщику в очередь готовых к вызову


    get - Если в очереди есть данные, отдает их
    Если нет, начинает ждать их появления и отдает контроль управления

    Более подробно:
    Вызывает функцию потребитель передавая ей первый елемент из очереди
    Если очередь елементов пуста, вставляет в очередь ожидающих геттеров себя же, вместе с переданным ему в аргументы
    потребителем.

    Идея заключается в том, что при отсутствии данных, вызов потребителя откладывается на более поздний
    момент, когда производитель положит данные в очередь.
"""
