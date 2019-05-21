import helper_functions as helper
import threading
import time
from ca_logging import log
from whiteboard import whiteboard


def loop_forever(whiteboard):
    whiteboard.service_started = True
    while whiteboard.service_started:
        time.sleep(.1)
    # print("stop client loop_forever")

def on_log(client, obj, level, string):
    helper.raise_error(client= client, level= level, error_msg=string)


class WhiteBoardClient:
    def __init__(self, name, subscribes, publishes):
        self.name = name
        self.publishes = publishes
        self.subscribes = subscribes
        self.service_started = False
        log.info("%s: init" % self.name)

    def subscribe(self, topics):
        for t in topics:
            whiteboard.subscribe(self, t)

    def unsubscribe(self):
        for topic in self.subscribes:
            whiteboard.unsubscribe(self, topic)

    def start_thread(self):
            t = threading.Thread(target=loop_forever, args=(self, ))
            t.start()

    def start_service(self):
        self.on_log = on_log
        self.subscribe(self.subscribes)
        self.start_thread()
        log.info("%s: started service" % self.name)

    def stop_service(self):
        self.unsubscribe()
        self.service_started = False

    def on_whiteboard_message(self, message, topic):
        helper.print_message(self.name, "received", message, topic)
        self.treat_message(message,topic)

    def treat_message(self, message, topic):
        log.error("$s: method treat_message should be overwriten in inherited classes!" % name)

    def publish(self, message):
        helper.print_message(self.name, "publishing", message, self.publishes)
        whiteboard.publish(message, self.publishes)

