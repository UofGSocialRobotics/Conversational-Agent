import broker_client as bc
import time
import random
import broker_config as config

def read_from_imaginary_thermometer():
    return 36 + random.uniform(0, 1)*4

class NLU(bc.Client_Dialog_System):
    def __init__(self, name, msg_subscribe_type, msg_publish_type):
        bc.Client_Dialog_System.__init__(self,name, msg_subscribe_type, msg_publish_type)


    def treat_msg(self,msg):
        temperature = read_from_imaginary_thermometer()
        print("\n\n%s: doing something with message and postiting result for DM\nResult is: %d"%(self.name,temperature))
        self.publish(str(temperature))


if __name__ == "__main__":
    my_dum_NLU = NLU("NLU",config.MSG.NLU,"m_ASR")
    my_dum_NLU.start_client()
    # my_dum_NLU.loop_forever()

    my_dum_NLU.loop_start()
    while True:
        temperature = read_from_imaginary_thermometer()
        my_dum_NLU.publish(str(temperature))
        time.sleep(10)
