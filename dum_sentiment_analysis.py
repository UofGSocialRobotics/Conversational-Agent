import whiteboard_client as wbc
from ca_logging import log


class SentimentAnalysis(wbc.WhiteBoardClient):
    def __init__(self, name, msg_subscribe_types, msg_publish_type):
        wbc.WhiteBoardClient.__init__(self, name, msg_subscribe_types, msg_publish_type)

    def treat_message(self, msg, topic):
        if "please" in msg.lower():
            new_msg = "NICE"
        else :
            new_msg = "NOT_NICE"
        self.publish(new_msg)


