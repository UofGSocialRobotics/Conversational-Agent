import whiteboard_client as wbc
import random

def read_from_imaginary_thermometer():
    return 36 + random.uniform(0, 1)*4

class DM(wbc.WhiteBoardClient):
    def __init__(self, name, msg_subscribe_types, msg_publish_type):
        wbc.WhiteBoardClient.__init__(self, name, msg_subscribe_types, msg_publish_type)
        self.from_NLU = None
        self.from_SA = None

    def treat_message(self, msg, topic):
        if "SA" in topic:
            self.from_SA = msg
        elif "NLU" in topic:
            self.from_NLU = msg
        if self.from_NLU and self.from_SA:
            nice = self.from_SA
            if self.from_NLU == "ASK_FEVER":
                temperature = read_from_imaginary_thermometer()
                if temperature > 38.5:
                    new_msg = "Yes: " + str(temperature) + ":" + nice
                else :
                    new_msg = "No: " + str(temperature) + ":" + nice
            else:
                new_msg = "DONT UNDERSTAND"
            self.publish(new_msg)


