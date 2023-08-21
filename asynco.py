from scheduler import Scheduler

sched = Scheduler()


def count_down(n):
    if n > 0:
        print('Down', n)
        # time.sleep(4)   # Blocking call (nothing else can run)
        sched.call_later(4, lambda: count_down(n - 1))


def count_up(stop):
    def _run(x):
        if x < stop:
            print('Up', x)
            # time.sleep(1)
            sched.call_later(1, lambda: _run(x + 1))
    _run(0)


sched.call_soon(lambda: count_down(5))
sched.call_soon(lambda: count_up(20))
sched.run()
