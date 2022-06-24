import time
import threading

class Timer:
    def __init__(self, sec, finish_condition_check=None, callback=None):
        self.finished = False
        self.ms = sec * 10
        self.finish_condition_check = finish_condition_check
        self.callback = callback # callback is run when time runs out.
        self.thread = threading.Thread(target=self.start_counting_down, args=())
    
    def start(self):
        self.thread.start()
    
    def start_counting_down(self):
        while not self.finished:
            if self.ms == 0:
                self.finished = True
                break
            if self.finish_condition_check != None:
                self.finished = self.finish_condition_check()
                if self.finished: break
            time.sleep(0.1)
            if self.ms > 0:
                self.ms -= 1
        if self.callback is not None:
            self.callback()
    
    def extend(self, sec):
        self.ms += sec * 10

    def join(self):
        self.thread.join()