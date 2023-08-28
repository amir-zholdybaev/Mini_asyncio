import time
from collections import deque
import heapq


class Scheduler:
    def __init__(self):
        self.ready = deque()     # Functions ready to execute
        self.sleeping = []       # Sleeping functions
        self.sequence = 0        # Used to break ties in priority queue

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


sched = Scheduler()     # Behind scenes scheduler object


def countdown(n):
    if n > 0:
        print('Down', n)
        sched.call_later(4, lambda: countdown(n - 1))   # time.sleep(4)


def countup(stop):
    def _run(x):
        if x < stop:
            print('Up', x)
            sched.call_later(1, lambda: _run(x + 1))    # time.sleep(1)
    _run(0)


sched.call_soon(lambda: countdown(5))
sched.call_soon(lambda: countup(20))
sched.run()


"""
    Scheduler - Решает какие функции нужно вызвать сразу, а какие вызвать позже в определенное время

    call_soon - Добавляет функцию в очередь готовых к выполнению

    call_later - Добавляет в очередь ждущих выполнения функцию, вместе с временем ее вызова в будущем

    run - Вызывает все готовые к вызову функции
    Если таковых нет, то берет ближайшую ожидающую вызова,
    ждет наступление времени ее вызова и вызывает
    Повторяет эти действия до тех пор, пока есть хоть одна готовая или ожидающая фукнция


    Подробнее:
    Достает все фукнции из очереди готовых и вызывает их
    Если в очереди готовых ничего нет, то достает ближайщую функцию из очереди ждущих,
    ждет наступление времени ее вызова, добавляет в очередь готовых, достает оттуда и вызывает
    Повторяет эти действия до тех пор, пока есть хоть одна функция в очереди готовых или ожидающих

    Еще более подробно:

    Запускает выполнение функций

    Запускает цикл, который выполняется пока в очереди готовых или ждущих функций что то есть

        Если в очереди готовых ничего нет:

            То из очереди ждущих, достает функцию, у которой самое ближайшее время вызова

            Вычисляет оставшееся до вызова время

            Если оно больше нуля, то делает паузу на это время, а после добавляет в очередь готовых

            Если оно равно или меньше нуля, то сразу добавляет в очередь готовых

        А после достает все функции из очереди готовых и вызывает

        Если в очереди готовых что то есть, то сразу достает все функции из очереди готовых и вызывает,
        пропуская выше описанные операции со функцией из очереди ждещих

        Цикл начинает новую итерацию
"""
