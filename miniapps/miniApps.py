#!/usr/bin/env python3
import inspect
import sys
import os
import argparse

cur_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
miniapp_dir = os.path.dirname(cur_dir)


class MiniApp:
    memgrow_app = os.path.join(miniapp_dir, "MemoryGrow", "memgrow")

    def __init__(self, sleep: int = None, memgrow: int = None, mulmat = None):
        self.sleep = sleep
        self.memgrow = memgrow
        self.mulmat = mulmat

    def __str__(self):
        s = "MiniApp Options:\n"
        s += "\tsleep: " +str(self.sleep) + "\n"
        s += "\tmemgrow: " + str(self.memgrow) + "\n"
        return s

    def sleep_cycle(self):
        print("sleep")

    @staticmethod
    def memgrow_cycle(self, memgrow: int) -> None:
        print("MemoryGrow")

        os.system("%s %d" % (MiniApp.memgrow_app, memgrow))

    def run(self):
        if self.sleep:
            self.sleep_cycle()

        if self.memgrow:
            self.memgrow_cycle(self.memgro)

        if self.mulmat:
            if len(sys.argv) - 1 < 4:
                print("Not enough argument for sleep, require <time>")
                sys.exit()
            else:
                matrixMultiplication(sys.argv[2], sys.argv[3], sys.argv[4])


def matrixMultiplication(size, calctime, sleeptime):
    print("MatrixMultiplication")
    os.system('cd ../MatrixMultiplication/ && make run size=' + str(size)+' calcSeconds=' + str(calctime)
              + ' sleepSeconds=' + str(sleeptime))


if __name__ == '__main__':

    import argparse

    parser = argparse.ArgumentParser(description='Slurm Simulator Run automation')

    parser.add_argument('-sleep', type=int, default=None,
                        help="seconds to sleep")

    parser.add_argument('-memgrow', type=int, default=None,
                        help="Grow MiB per seconds")
#   parser.add_argument('-v', '--verbose', action='store_true',
#                        help="turn on verbose logging")

    args = parser.parse_args()
    print(args)
    miniapp = MiniApp(**vars(args))
    print(miniapp)
    miniapp.run()


