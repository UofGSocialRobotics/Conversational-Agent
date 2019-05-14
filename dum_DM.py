import broker_client as bc
import helper_functions as helper

class DM(bc.ClientLocalBroker):
    def __init__(self,name,msg_subscribe_type,msg_publish_type,local_broker):
        bc.ClientLocalBroker.__init__(self,name,msg_subscribe_type,msg_publish_type,local_broker)

    def treat_message(self,msg,topic):
        msg_value = float(msg)
        displayed_msg = "Temperature is: %.2f."%msg_value
        if msg_value > 38.5:
            displayed_msg +=  " DANGER!!! Has fiever!"
        self.publish(displayed_msg)

# if __name__ == "__main__":
#     my_dum_DM = DM("my_dum_DM","m_NLU","m_DM")
#     my_dum_DM.start_client()
#     my_dum_DM.loop_forever()
