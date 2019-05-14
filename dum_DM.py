import whiteboard_client as wbc

class DM(wbc.WhiteBoardClient):
    def __init__(self, name, msg_subscribe_type, msg_publish_type, whiteboard):
        wbc.WhiteBoardClient.__init__(self, name, msg_subscribe_type, msg_publish_type, whiteboard)

    def treat_message(self, msg, topic):
        msg_value = float(msg)
        displayed_msg = "Temperature is: %.2f."%msg_value
        if msg_value > 38.5:
            displayed_msg +=  " DANGER!!! Has fiever!"
        self.publish(displayed_msg)

# if __name__ == "__main__":
#     my_dum_DM = DM("my_dum_DM", "m_NLU", "m_DM")
#     my_dum_DM.start_client()
#     my_dum_DM.loop_forever()
