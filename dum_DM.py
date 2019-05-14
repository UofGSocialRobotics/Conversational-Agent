import whiteboard_client as wbc
import random

def read_from_imaginary_thermometer():
    return 36 + random.uniform(0, 1)*4

class DM(wbc.WhiteBoardClient):
    def __init__(self, name, msg_subscribe_type, msg_publish_type, whiteboard):
        wbc.WhiteBoardClient.__init__(self, name, msg_subscribe_type, msg_publish_type, whiteboard)

    def treat_message(self, msg, topic):
        if msg == "ASK_FEVER":
            temperature = read_from_imaginary_thermometer()
            if temperature > 38.5:
                new_msg = "Yes: " + str(temperature)
            else :
                new_msg = "No: " + str(temperature)
        else:
            new_msg = "DONT UNDERSTAND"
        self.publish(new_msg)


