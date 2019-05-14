import broker_client as bc
import time
import random

def read_from_imaginary_thermometer():
    return 36 + random.uniform(0, 1)*4

class NLU(bc.ClientLocalBroker):
    def __init__(self, name, msg_subscribe_type, msg_publish_type, local_broker):
        bc.ClientLocalBroker.__init__(self,name, msg_subscribe_type, msg_publish_type, local_broker)

    def treat_message(self,msg,topic):
        temperature = read_from_imaginary_thermometer()
        # print("\n\n%s: doing something with message and postiting result for DM\nResult is: %d"%(self.name,temperature))
        self.publish(str(temperature))



