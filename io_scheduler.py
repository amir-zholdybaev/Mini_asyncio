import time
from collections import deque
import heapq
from select import select


class Scheduler:
    def __init__(self):
        self.ready = deque()     # Functions ready to execute
        self.sleeping = []       # Sleeping functions
        self.sequence = 0 
        self._read_waiting = { }
        self._write_waiting = { }

    def call_soon(self, func):
        self.ready.append(func)

    def call_later(self, delay, func):
        self.sequence += 1
        deadline = time.time() + delay     # Expiration time
        heapq.heappush(self.sleeping, (deadline, self.sequence, func))

    def read_wait(self, fileno, func):
        self._read_waiting[fileno] = func   # Trigger func() when fileno is readable

    def write_wait(self, fileno, func):
        self._write_waiting[fileno] = func  # Trigger func() when fileno is writeable

    def run(self):
        while (self.ready or self.sleeping or self._read_waiting or self._write_waiting):
            if not self.ready:
                # Find the nearest deadline
                if self.sleeping:
                    deadline, _, func = self.sleeping[0]
                    timeout = deadline - time.time()
                    if timeout < 0:
                        timeout = 0
                else:
                    timeout = None     # Wait forever

                # Wait for I/O (and sleep)
                can_read, can_write, _ = select(self._read_waiting, self._write_waiting, [], timeout)

                for fd in can_read:
                    self.ready.append(self._read_waiting.pop(fd))
                for fd in can_write:
                    self.ready.append(self._write_waiting.pop(fd))

                # Check for sleeping tasks
                now = time.time()
                while self.sleeping:
                    if now > self.sleeping[0][0]:
                        self.ready.append(heapq.heappop(self.sleeping)[2])
                    else:
                        break

            while self.ready:
                func = self.ready.popleft()
                func()

    def new_task(self, coro):
        self.ready.append(Task(coro))   # Wrapped coroutine

    async def sleep(self, delay):
        self.call_later(delay, self.current)  
        self.current = None
        await switch()   # Switch to a new task

    async def recv(self, sock, maxbytes):
        self.read_wait(sock, self.current)
        self.current = None
        await switch()
        return sock.recv(maxbytes)

    async def send(self, sock, data):
        self.write_wait(sock, self.current)
        self.current = None
        await switch()
        return sock.send(data)

    async def accept(self, sock):
        self.read_wait(sock, self.current)
        self.current = None
        await switch()
        return sock.accept()


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


from socket import *
async def tcp_server(addr):
    sock = socket(AF_INET, SOCK_STREAM)
    sock.bind(addr)
    sock.listen(1)
    while True:
        client, addr = await sched.accept(sock)
        print('Connection from', addr)
        sched.new_task(echo_handler(client))


async def echo_handler(sock):
    while True:
        data = await sched.recv(sock, 10000)
        if not data:
            break
        await sched.send(sock, b'Got:' + data)
    print('Connection closed')
    sock.close()


sched.new_task(tcp_server(('', 30000)))
sched.run()


"""
    Суть планировщика при работе с корутинами, заключается в том, чтобы готовую к вызову корутину отметить как
    текущую/исполняемую и вызвать ее. В случае если в коде этой корутины встречается метод планировщика, который
    требует большого времени для исполнения, то в коде этого метода текущая корутина кладется в одну из очередей
    ожидания планировщика и перестает быть текущей. После этого метод планировщика отдает контроль управления, в то
    место, где был вызван. После чего сразу же и корутина отдает контроль. Когда наступает время корутины выйти из
    очереди, она снова отмечается текущей и вызывается с того места где была приостановлена ранее. Этим местом
    является вызов метода планировщика. Поэтому метод планировщика снова вызывается, с того места, где был приостановлен
    ранее, возвращает результат, тем самым снова отдает контроль управления текущей корутине. Корутина получает
    результат из метода и продолжает свою работу, обрабатывая результат.

    Здесь в коде планировщика все также как и в файле coro_callback.py, только внесены определенные изменения и
    дополнения для работы с вводом/выводом сокетов. Добавлены методы для принятия соединения, считывания, а
    также отправки данных. Добавлены две очереди - одна для сокетов ожидающих чтения, другая для сокетов ожидающих
    записи. Также добавлены два метода, кладущие сокеты в эти очереди.

    Основной передел коснулся метода run.
"""