import helper_functions as helper
import threading
import time
from ca_logging import log
from whiteboard import whiteboard
import time
from termcolor import colored

# def on_log(client, obj, level, string):
#     helper.raise_error(client= client, level= level, error_msg=string)


class WhiteBoardClient:
    def __init__(self, name, subscribes, publishes, resp_time=False):
        self.name = name
        self.publishes = publishes
        self.subscribes = subscribes
        self.service_started = False
        self.time_start = None
        self.resp_time = resp_time
        # log.info("%s: init" % self.name)

    def subscribe(self, topics):
        for t in topics:
            whiteboard.subscribe(self, t)

    def unsubscribe(self):
        for topic in self.subscribes:
            whiteboard.unsubscribe(self, topic)

    def start_thread(self):
        t = threading.Thread(name=self.name, target=self.loop_forever)
        t.start()

    def start_service(self):
        # self.on_log = on_log
        self.subscribe(self.subscribes)
        self.start_thread()
        log.info("%s: started service" % self.name)

    def stop_service(self):
        self.unsubscribe()
        self.service_started = False

    def on_whiteboard_message(self, message, topic):
        if ("DataCollector_in" not in self.name) or ("DataCollector_in" in self.name and "data_recommendation" in message.__str__()):
            helper.print_message(self.name, "received", message, topic)
            self.treat_message(message,topic)

    def treat_message(self, message, topic):
        # log.error("$s: method treat_message should be overwriten in inherited classes!" % self.name)
        # print("treat_message WhiteBoardClient %s" % self.name)
        self.time_start = time.time()

    def publish(self, message, topic=None):
        # helper.print_message(self.name, "publishing", message, self.publishes)
        if self.resp_time:
            resp_time = time.time() - self.time_start
            color = "green" if resp_time < 0.5 else "red"
            print(colored("%s response time: " % self.name, "green") + colored( "%.3f sec" % resp_time, color) )
        if isinstance(self.publishes, list):
            if not topic:
                log.critical("No topic provided. %s can publish on :" % self.name + self.publishes)
            else:
                whiteboard.publish(message, topic)
        else:
            whiteboard.publish(message, self.publishes)

    def loop_forever(self):
        self.service_started = True
        while self.service_started:
            time.sleep(.1)
        # print("stop client loop_forever")
