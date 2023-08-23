from async_queue_with_error import AsyncQueue, sched, QueueClosed

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
