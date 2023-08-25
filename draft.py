# class Awaitable:
#     def __await__(self):
#         print('awaitable')
#         yield 'hello'
#         print('awaitable 2')
#         return 1
#         print('awaitable 3')


# async def switch():
#     print('switch')
#     num = await Awaitable()
#     print('switch 2')
#     return num


# async def countdown(n):
#     while n > 0:
#         print('Down', n)
#         num = await switch()
#         print(num)
#         print('oppa')
#         n -= 1


# coro = countdown(5)

# print(coro.send(None))
# print(coro.send(None))


def coro():
    print('coro')
    yield
    print('coro 2')
    return 100


def coro_from():
    count = 0

    while count < 5:
        print('coro_from')

        # for i in coro():
        #     yield

        num = yield from coro()
        print('num: ', num)

        count += 1
        print('coro_from 2')


it = coro_from()

it.__next__()
it.__next__()
