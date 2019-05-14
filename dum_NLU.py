import whiteboard_client as wbc
import random

def read_from_imaginary_thermometer():
    return 36 + random.uniform(0, 1)*4

class NLU(wbc.WhiteBoardClient):
    def __init__(self, name, msg_subscribe_type, msg_publish_type, whiteboard):
        wbc.WhiteBoardClient.__init__(self,name, msg_subscribe_type, msg_publish_type, whiteboard)

    def treat_message(self,msg,topic):
        temperature = read_from_imaginary_thermometer()
        # print("\n\n%s: doing something with message and postiting result for DM\nResult is: %d"%(self.name,temperature))
        self.publish(str(temperature))



