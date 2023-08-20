import time


def count_down(n):
    while n > 0:
        print('Down', n)
        time.sleep(1)
        n -= 1


def count_up(stop):
    x = 0
    while x < stop:
        print('Up', x)
        time.sleep(1)
        x += 1


# Sequential execution
count_down(5)
count_up(5)
