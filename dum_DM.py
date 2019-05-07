import clientdialogsystem as cds

class DM(cds.Client_Dialog_System):
    def __init__(self,name,msg_publish_type,msg_subscribe_type):
        cds.Client_Dialog_System.__init__(self,name,msg_publish_type,msg_subscribe_type)

    def _treat_msg(self,msg):
        msg_value = float(msg.payload.decode('utf-8'))
        displayed_msg = "Temperature is: %.2f."%msg_value
        if msg_value > 38.5:
            displayed_msg +=  " DANGER!!! Has fiever!"
        print(displayed_msg)

my_dum_DM = DM("my_dum_DM","m_DM","m_NLU")
my_dum_DM.start_client()
my_dum_DM._loop_forever()