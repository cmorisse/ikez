# coding: utf-8
import sys

__author__ = 'cmorisse'

import threading
import time

class CursorAnimation(threading.Thread):
    def __init__(self):
        self.flag = True
        self.idx = 0
        threading.Thread.__init__(self)

    def run(self):
        while self.flag:
            print "\rProcessing: %s%s" % ("." * (self.idx % 8)," " * (7 - (self.idx % 8)),),
            sys.stdout.flush()
            self.idx += 1
            time.sleep(0.2)

    def stop(self):
        self.flag = False

if __name__ == '__main__':
    spin = CursorAnimation()


    # Start Animation
    spin.start()

    # Do something here
    # Example: sleep
    time.sleep(5)

    # Stop Animation
    spin.stop()