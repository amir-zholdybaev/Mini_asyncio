from collections import deque
from scheduler import Scheduler

sched = Scheduler()     # Behind scenes scheduler object


class QueueClosed(Exception):
    pass


class Result:
    def __init__(self, value=None, exc=None):
        self.value = value
        self.exc = exc

    def result(self):
        if self.exc:
            raise self.exc
        else:
            return self.value


class AsyncQueue:
    def __init__(self):
        self.items = deque()
        self.waiting = deque()    # All getters waiting for data
        self._closed = False    # Can queue be used anymore?

    def close(self):
        self._closed = True
        if self.waiting and not self.items:
            for func in self.waiting:
                sched.call_soon(func)

    def put(self, item):
        if self._closed:
            raise QueueClosed()

        self.items.append(item)
        if self.waiting:
            func = self.waiting.popleft()
            # Do we call it right away? No. Schedule it to be called.
            sched.call_soon(func)

    def get(self, callback):
        # Wait until an item is available. Then return it
        # Question: How does a closed queue interact  with get()
        if self.items:
            callback(Result(value=self.items.popleft()))  # Good result
        else:
            # No items available (must wait)
            if self._closed:
                callback(Result(exc=QueueClosed()))  # Error result
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
            q.close()   # Means no more items will be produced

    _run(0)


"""
    Производитель генерирует данные и кладет их в очередь и оповещает потребителя о положенных данных,
    если есть ждущий потребитель
    Делает он это каждые n секунд и до тех пор, пока не достигнет конца счетчика
    Когда счетчик закончен, завершает свою работу и закрывает очередь
"""


def consumer(q):
    def _consume(result):
        try:
            item = result.result()
            print('Consuming', item)
            sched.call_soon(lambda: consumer(q))

        except QueueClosed:
            print('Consumer done')

    q.get(callback=_consume)


"""
    Потребитель пытается получить данные
    Если в очереди есть готовые данные, он берет их, обрабатывает и запрашивает по новой (sched.call_soon(lambda: consumer(q)))
    Если в очереди данных нет, он их ждет
    Повторяет он эти действия до тех пор, пока производитель данных не прекратит свою работу
    Когда производитель завершает свою работу, то он закрывает очередь и потребитель вместо данных получает ошибку,
    отлавливает ее и заканчивает работу
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

    close - Закрывает очередь
    Если в очереди ждущих геттеров что то есть, а в очереди елементов пусто, вызывает оставшиеся в ожидании геттеры
    Геттер же в свою очередь передает потребителю объект result с ошибкой и потребитель завершает свою работу


    put - Кладет данные в очередь, не проверяя ее заполненность
    Если есть ждущий геттер, оповщает его о появлении данных

    Более подробно:
    Смотрит не закрыта ли очередь, если закрыта, то вызывает исключение QueueClosed()
    Вставляет данные в очередь, не проверяя ее заполненность
    Если в очереди ожидающих геттеров есть что то, берет первый и отдает его планировщику в очередь готовых к вызову


    get - Если в очереди есть данные, отдает их
    Если нет, начинает ждать их появления и отдает контроль управления
    Если очередь пуста и закрыта отдает ошибку QueueClosed()

    Более подробно:
    Вызывает функцию потребитель передавая ей объект result с данными

    Если очередь пуста и закрыта, вызывает потребителя, передавая ему объект result с ошибкой
    Если очередь пуста, но открыта, вставляет в очередь ожидающих геттеров себя же, вместе с
    переданным ему в аргументы потребителем.

    Идея заключается в том, что при отсутствии данных, вызов потребителя откладывается на более поздний
    момент, когда производитель положит данные в очередь.
"""
