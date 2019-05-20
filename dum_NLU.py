import whiteboard_client as wbc
import helper_functions as helper
from ca_logging import log

class NLU(wbc.WhiteBoardClient):
    def __init__(self, subscribes, publishes, clientid):
        subscribes = helper.append_c_to_elts(subscribes, clientid)
        publishes = publishes + clientid
        wbc.WhiteBoardClient.__init__(self, name="NLU"+clientid, subscribes=subscribes, publishes=publishes)

    def treat_message(self,msg,topic):
        msg_lower = msg.lower()
        if "fever" in msg_lower or "temperature" in msg_lower:
            new_msg = "ASK_FEVER"
        else :
            new_msg = "OTHER"
        self.publish(new_msg)



