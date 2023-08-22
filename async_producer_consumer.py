# aproducer.py
#
# Async Producer-consumer problem.
# Challenge: How to implement the same functionality, but no threads.

from async_queue import AsyncQueue, sched

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
    Делает он это каждые n секунд и до тех пор, пока не достигнет конца генерации
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
    Повторяет он эти действия до тех пор, пока производитель не прекратит их производить
"""

sched.call_soon(lambda: producer(aq, 10))
sched.call_soon(lambda: consumer(aq,))
sched.run()
