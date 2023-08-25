# aproducer.py
#
# Async Producer-consumer problem.
# Challenge: How to implement the same functionality, but no threads.

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
    Если нет, начинает ждать их появления
    Если очередь пуста и закрыта отдает ошибку QueueClosed()

    Более подробно:
    Вызывает функцию потребитель передавая ей объект result с данными

    Если очередь пуста и закрыта, вызывает потребителя, передавая ему объект result с ошибкой
    Если очередь пуста, но открыта, вставляет в очередь ожидающих геттеров себя же, вместе с
    переданным ему в аргументы потребителем.

    Идея заключается в том, что при отсутствии данных, вызов потребителя откладывается на более поздний
    момент, когда производитель положит данные в очередь.
"""
