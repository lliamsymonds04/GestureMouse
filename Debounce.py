import time

class Debounce:
    def __init__(self, wait_time):
        self.wait_time = wait_time
        self.last_time = 0

    def activate(self):
        self.last_time = time.time()

    def __bool__(self):
        return time.time() - self.last_time > self.wait_time