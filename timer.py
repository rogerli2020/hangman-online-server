import time
import threading

class Timer:
    def __init__(self, sec, finish_condition_check=None, callback=None, send_updates=False, round=None):
        self.finished = False
        self.ms = sec * 10
        self.finish_condition_check = finish_condition_check
        self.callback = callback # callback is run when time runs out.
        self.thread = threading.Thread(target=self.start_counting_down, args=())

        self.send_updates = send_updates
        self.round = round
    
    def start(self):
        self.thread.start()
    
    def start_counting_down(self):
        while not self.finished and not self.round.stopped_prematurely:
            if self.ms == 0:
                self.finished = True
                break
            if self.finish_condition_check != None:
                self.finished = self.finish_condition_check()
                if self.finished: break
            time.sleep(0.1)
            if self.ms > 0:
                self.ms -= 1
            if self.ms % 10 == 0 and self.send_updates:
                self.send_update()
        if self.callback is not None and self.ms <= 0:
            self.callback()
    
    def send_update(self):
        msg = {
            "msg_type": "update",
            "update_type": "timer",
            "content": int(self.ms / 10)
        }
        self.round.msg_pool.push(self.round.p1, msg)
        self.round.msg_pool.push(self.round.p2, msg)

    def extend(self, sec):
        self.ms += sec * 10

    def join(self):
        self.thread.join()