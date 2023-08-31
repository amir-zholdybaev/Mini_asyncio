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
    место, где был вызван. После чего и эта корутина отдает контроль. Когда наступает время корутины выйти из
    очереди, она снова отмечается текущей и вызывается с того места где была приостановлена ранее. Этим местом
    является вызов метода планировщика. Поэтому метод планировщика снова вызывается, с того места, где был приостановлен
    ранее, возвращает результат, тем самым снова отдает контроль управления текущей корутине. Корутина получает
    результат из метода и продолжает свою работу, с места вызова метода, получая от него результат и обрабатывая его.

    Здесь в коде планировщика все также как и в файле coro_callback.py, только внесены определенные изменения и
    дополнения для работы с вводом/выводом сокетов. Добавлены методы для принятия соединения(accept()),
    считывания(recv()), а также отправки данных(send()). Добавлены две очереди - одна для сокетов ожидающих
    чтения(self._read_waiting), другая для сокетов ожидающих записи(self._write_waiting). Также добавлены два метода,
    кладущие сокеты в эти очереди. Эти очереди по сути словари, ключом в которых являются сокеты, а значением корутины,
    из которых были вызваны методы для записи или чтения данных из этих сокетов.

    run - Основной передел коснулся метода run.
    Здесь также вычисляется оставшееся время до вызова ближайшей спящей корутины, но теперь вместо вызыва метода time.sleep()
    на время осташееся до вызова, вызывается функция select(), куда передается оставшееся до вызова время в качестве
    таймаута. Функция select() - это способ отслеживать готовность сокетов к операциям ввода или вывода. Она принимает
    список сокетов, ожидающих чтения, список сокетов, ожидающих возможности отправки данных, список ошибок, а также timeout -
    время на которое функция select() будет блокировать поток, ожидая готовности хотябы одного из сокетов.
    Таким образом мы не просто блокируем поток кода на время оставшееся до вызова корутины, но и смотрим нет ли входящих
    подключений, соединений или возможности отправки данных.

    Сначала мы вычесляем время оставшееся до вызова корутины. Называем его timeout. Если timeout меньше нуля, то присваиваем
    ему значение 0, чтобы не передавать в функцию select() timeout с отрицательным значением.

    Если у нас очереди спящих и готовых корутин пустуют, то присваиваем timeout значение None и передаем его функции select()
    Если передать функции select() в качестве timeout значение None, то она будет блокировать поток постоянно, до тех пор
    пока не появиться хотябы одного готового сокета.

    И это логично. Ведь если нет ни одной готовой к исполнению или ожидающей задачи, то это время лучше с пользой. В данном
    случае ожидать запроса на подключение, прихода данных или возможности их отправки.

    После того как хотябы от одного сокета поступил сигнал, функция select() прекращает блокировать поток и возвращает
    список готовых к общению сокетов. Один список сокетов, список ожидавших подключения либо прихода
    данных(can_read), второй ожидавших возможности отправки данных(can_write). Один из списков может быть пустым. Например
    если нет сокетов получивших возможность отправки данных, то список can_write является пустым, а в списке can_read
    находятся сокеты, к которым поступил запрос на подключение либо пришли данные. Далее все корутины, связанные с сокетами
    в этих списках помещаются в очередь готовых к вызову.

    После этих операций завускается цикл выполняющийся до тех пор, пока в очереди ожидающих(спящих) корутин что то есть.
    В теле этого цикла сравнивается текущее время и время вызова ближайшей к пробуждению корутины. Если текущее время
    больше времени вызова этой корутины, то есть если время пробуждения корутины наступило, то она прекладывается в очередь
    готовых к вызову. И так этот цикл продолжается до тех пор, пока не наткнется на корутину, время вызова которой еще
    не настало либо пока список спящих корутин не станет пустым.

    В конце концов запускается цикл, вызывающий все готовые к выполнению корутины, предварительно доставая их из очереди
    готовых.

    recv - Этот метод кладет сокет, ожидающий прихода данных и связанную с ним корутину в очередь(словарь) ожидающих
    прихода данных либо подключения (self._read_waiting). После делает корутину не текущей(неисполняемой в данный момент),
    так как она теперь ожидает. После отдает контроль управления корутине, а та в свою очредь сразу же отдает контроль
    управления планировщику. После того как к сокету поступят данные, связанная с ним корутина будет вызвана.
    Свою работу она начнет на том же месте, где остановилась ранее. Она сразу же вызовет вызовет метод recv(). Метод recv()
    начнет свою работу с того места где отдал контроль управления корутине в прошлый раз. Он считает пришедшие данные, с
    сокета, который их ожидал и вернет их оператором return, тем самым отдав данные и контроль управления корутине.
    Та в свою очередь получит данные в том месте, где вызывала метод recv() и будет их обрабатывать.

    send() - Работает по тому же принципу что и метод recv(), только задействует сокет для отправки данных получателю.
    И кладет сокет, ожидающий возможности отправки данных в очередь self._write_waiting.

    accept() - Работает по тому же принципу что и метод recv(), только задействует серверный сокет для принятия подключения
    от клиентского сокета.
"""