import whiteboard_client as wbc
import random
import helper_functions as helper
from ca_logging import log

def read_from_imaginary_thermometer():
    return 36 + random.uniform(0, 1)*4

class DM(wbc.WhiteBoardClient):
    def __init__(self, subscribes, publishes, clientid):
        subscribes = helper.append_c_to_elts(subscribes,clientid)
        publishes = publishes + clientid
        wbc.WhiteBoardClient.__init__(self, "DM"+clientid, subscribes, publishes)
        self.from_NLU = None
        self.from_SA = None

    def treat_message(self, msg, topic):
        if "SA" in topic:
            self.from_SA = msg
        elif "NLU" in topic:
            self.from_NLU = msg

        # Wait for both SA and NLU messages before sending something back to the whiteboard
        if self.from_NLU and self.from_SA:
            if "pos" in self.from_SA:
                nice = "NICE"
            else:
                nice = "NOT_NICE"
            if self.from_NLU == "ASK_FEVER":
                temperature = read_from_imaginary_thermometer()
                if temperature > 38.5:
                    new_msg = "Yes: " + str(temperature) + ":" + nice
                else :
                    new_msg = "No: " + str(temperature) + ":" + nice
            else:
                new_msg = "DONT UNDERSTAND"
            self.from_NLU = None
            self.from_SA = None
            self.publish(new_msg)


