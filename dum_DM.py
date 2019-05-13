import broker_client as bc

class DM(bc.Client_Dialog_System):
    def __init__(self,name,msg_subscribe_type,msg_publish_type):
        bc.Client_Dialog_System.__init__(self,name,msg_subscribe_type,msg_publish_type)

    def treat_msg(self,msg):
        msg_value = float(msg.payload.decode('utf-8'))
        displayed_msg = "Temperature is: %.2f."%msg_value
        if msg_value > 38.5:
            displayed_msg +=  " DANGER!!! Has fiever!"
        print(displayed_msg)
        print("Will send message back to client.")
        self.publish(displayed_msg)

if __name__ == "__main__":
    my_dum_DM = DM("my_dum_DM","m_NLU","m_DM")
    my_dum_DM.start_client()
    my_dum_DM.loop_forever()
