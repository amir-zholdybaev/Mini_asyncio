import asyncio


async def hello():
    await asyncio.sleep(1)
    print("Hello")


async def hello_2():
    await asyncio.sleep(2)
    print("Hello 2")


async def wrapper():
    print('wrapper 1')
    await hello()
    print('wrapper 2')


async def wrapper_2():
    print('wrapper 3')
    await hello_2()
    print('wrapper 4')


async def main():
    # task1 = asyncio.create_task(hello())
    # task2 = asyncio.create_task(hello2())
    await asyncio.gather(wrapper(), wrapper_2())


asyncio.run(main())
