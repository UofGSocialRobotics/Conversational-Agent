import whiteboard_client as wbc


class NLU(wbc.WhiteBoardClient):
    def __init__(self, name, msg_subscribe_types, msg_publish_type):
        wbc.WhiteBoardClient.__init__(self,name, msg_subscribe_types, msg_publish_type)

    def treat_message(self,msg,topic):
        msg_lower = msg.lower()
        if "fever" in msg_lower or "temperature" in msg_lower:
            new_msg = "ASK_FEVER"
        else :
            new_msg = "OTHER"
        self.publish(new_msg)



