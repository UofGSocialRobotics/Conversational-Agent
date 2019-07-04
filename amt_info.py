import whiteboard_client as wbc
import helper_functions as helper
import json


class AMT_info(wbc.WhiteBoardClient):
    def __init__(self, subscribes, publishes, clientid, ack_msg):
        subscribes = helper.append_c_to_elts(subscribes, clientid)
        publishes = publishes + clientid
        wbc.WhiteBoardClient.__init__(self, name="AMT_info"+clientid, subscribes=subscribes, publishes=publishes)
        self.amt_id = None
        self.ack_msg = ack_msg

    def treat_message(self, msg, topic):
        self.amt_id = msg["amt_id"]
        # print(self.amt_id)
        self.publish(self.ack_msg)



