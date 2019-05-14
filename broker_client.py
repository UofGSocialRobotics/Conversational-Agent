import helper_functions as helper
import threading
import time

def loop_forever(local_broker):
    local_broker.service_started = True
    while local_broker.service_started :
        time.sleep(1)


class ClientLocalBroker:
    def __init__(self, name, msg_subscribe_type, msg_publish_type, local_broker):
        self.name = name
        self.msg_publish_type = msg_publish_type
        self.msg_subscribe_type = msg_subscribe_type
        self.local_broker = local_broker
        self.service_started = False
        print("%s: init"%self.name)

    def subscribe(self, topic):
        self.local_broker.subscribe(self, topic)

    def unsubscribe(self):
        self.local_broker.unsubscribe(self, self.msg_subscribe_type)

    def start_thread(self):
            t = threading.Thread(target=loop_forever, args=(self, ))
            t.start()

    def start_service(self):
        self.subscribe(self.msg_subscribe_type)
        self.start_thread()
        print("%s: started service"%self.name)

    def stop_service(self):
        self.unsubscribe()
        self.service_started = False

    def on_local_message(self, message, topic):
        helper.print_message(self.name, "received", message, topic)
        self.treat_message(message,topic)

    def treat_message(self, message, topic):
        print("----------------- ERR: method treat_message should be overwritter in inherited classes! -----------------")

    def publish(self, message):
        helper.print_message(self.name, "publishing", message, self.msg_publish_type)
        self.local_broker.publish(message, self.msg_publish_type)

