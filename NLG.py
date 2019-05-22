import whiteboard_client as wbc
import helper_functions as helper

class NLG(wbc.WhiteBoardClient):
    def __init__(self, subscribes, publishes, clientid):
        subscribes = helper.append_c_to_elts(subscribes, clientid)
        publishes = publishes + clientid
        wbc.WhiteBoardClient.__init__(self, "NLG"+clientid, subscribes, publishes)

    def treat_message(self, message, topic):
        sentence = message
        self.publish(sentence)

