"""
Execute a series of generators that feed into each other such that each one gets
its own thread.

Remember that (1) due to the GIL this won't make you any faster unless your
generators are doing mostly I/O or calling into C and (2) because it uses
threads, it won't play well with Tornado code. Mostly it just lets you express
your data pipeline in a nice way
"""

from Queue import Queue
from threading import Thread
from functools import partial

class Pipeline(object):

    EOF = [] # just a unique object for 'is' comparisons

    def __init__(self, gens, bufsize=100):
        self.bufsize = bufsize

        self.qs = [ Queue(self.bufsize) for x in gens ]

        pairs = zip(self.qs, self.qs[1:])

        self.jobthreads = []

        # first generator is a special case
        self.jobthreads.append(
            Thread(target=self.genthread, args=(gens[0], self.qs[0]))
        )

        self.jobthreads.extend( Thread(target=self.jobthread, args=(fn, iq, oq))
                                for (fn, (iq, oq))
                                in zip(gens[1:], pairs) )

        for x in self.jobthreads:
            x.daemon = True
            x.start()

    def genthread(self, fn, oq):
        return self.wraptry(fn, oq)

    def jobthread(self, fn, iq, oq):
        return self.wraptry(fn, iq, oq)

    def wraptry(self, fn, *qs):
        try:
            return fn(*qs)
        except:
            qs[-1].put(self.EOF)
            raise

    def __iter__(self):
        while True:
            x = self.qs[-1].get()

            if x is self.EOF:
                break

            yield x

        # we if got the EOF, so did everybody else so they should be done
        for x in self.jobthreads:
            x.join()

class Generator(object):
    """
    Generator(x+5 for x in xrange(15))
    """
    def __init__(self, gen):
        self.gen = gen

    def __call__(self, oq):
        for x in self.gen:
            oq.put(x)

        oq.put(Pipeline.EOF)

class GeneratorMapper(object):
    """
    GeneratorMapper(lambda it: (x for x in it if isbacon(x)))
    """
    def __init__(self, l):
        self.l = l

    def __call__(self, iq, oq):
        def _gen():
            while True:
                x = iq.get()
                if x is Pipeline.EOF:
                    break
                yield x
                iq.task_done()

        primed = self.l(_gen())

        while True:
            try:
                x = primed.next()
                oq.put(x)
            except StopIteration:
                # we read out a Pipeline.EOF but didn't ack it, so ack it now
                oq.put(Pipeline.EOF)
                iq.task_done()
                break

def Mapper(fn):
    def _gen(it):
        return (fn(x) for x in it)
    return GeneratorMapper(_gen)

class MultiMapper(object):
    """
    Run the callable in a thread pool. n.b. that you lose order when you use
    this, and the GIL keeps you from getting any speed increase unless you're
    spending all of your time in C or I/O
    """
    def __init__(self, l, count):
        self.threads = []

        self.pool_q = Queue()

        for x in range(count):
            t = Thread(target=partial(self.target, l))
            t.daemon = True
            t.start()

            self.threads.append(t)

    def target(self, l):
        while True:
            got = self.pool_q.get()

            if got is Pipeline.EOF:
                self.pool_q.task_done()
                return

            item, oq, ack = got
            calculated = l(item)
            oq.put(calculated)
            self.pool_q.task_done()
            ack()

    def __call__(self, iq, oq):
        while True:
            got = iq.get()

            if got is Pipeline.EOF:

                for t in self.threads:
                    # we need each of our threads to see this, but they all pull
                    # from the same queue. so just add one message for each to
                    # read
                    self.pool_q.put(Pipeline.EOF)

                for t in self.threads:
                    t.join()

                oq.put(Pipeline.EOF)
                iq.task_done()
                return

            self.pool_q.put((got, oq, iq.task_done))

def proc1(iq, oq):
    while True:
        x = iq.get()

        if x is Pipeline.EOF:
            oq.put(x)
            iq.task_done()
            return

        oq.put(x*2)
        iq.task_done()

if __name__ == '__main__':
    p = Pipeline([
        Generator(xrange(50000)),
        proc1,
        GeneratorMapper(lambda it: (x-1 for x in it)),
        Mapper(lambda x: x*2),
    ])
    #p = Pipeline([gen])

    for x in p:
        print x

