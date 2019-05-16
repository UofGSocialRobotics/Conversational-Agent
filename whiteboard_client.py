import helper_functions as helper
import threading
import time
from ca_logging import log

def loop_forever(whiteboard):
    whiteboard.service_started = True
    while whiteboard.service_started :
        time.sleep(1)


class WhiteBoardClient:
    def __init__(self, name, msg_subscribe_type, msg_publish_type, whiteboard):
        self.name = name
        self.msg_publish_type = msg_publish_type
        self.msg_subscribe_type = msg_subscribe_type
        self.whiteboard = whiteboard
        self.service_started = False
        log.info("%s: init" % self.name)

    def subscribe(self, topic):
        self.whiteboard.subscribe(self, topic)

    def unsubscribe(self):
        self.whiteboard.unsubscribe(self, self.msg_subscribe_type)

    def start_thread(self):
            t = threading.Thread(target=loop_forever, args=(self, ))
            t.start()

    def start_service(self):
        self.subscribe(self.msg_subscribe_type)
        self.start_thread()
        log.info("%s: started service" % self.name)

    def stop_service(self):
        self.unsubscribe()
        self.service_started = False

    def on_whiteboard_message(self, message, topic):
        helper.print_message(self.name, "received", message, topic)
        self.treat_message(message,topic)

    def treat_message(self, message, topic):
        log.warning("%s: method treat_message should be overwritter in inherited classes! -----------------" % self.name)

    def publish(self, message):
        helper.print_message(self.name, "publishing", message, self.msg_publish_type)
        self.whiteboard.publish(message, self.msg_publish_type)

