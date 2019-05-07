import clientdialogsystem as cds
import time
import random

def read_from_imaginary_thermometer():
    return 36 + random.uniform(0, 1)*4

class NLU(cds.Client_Dialog_System):
    def __init__(self, name, msg_publish_type, msg_subscribe_type):
        cds.Client_Dialog_System.__init__(self,name, msg_publish_type, msg_subscribe_type)


    def _treat_msg(self,msg):
        temperature = read_from_imaginary_thermometer()
        print("\n\n%s: doing something with message and postiting result for DM\nResult is: %d"%(self.name,temperature))
        my_dum_NLU.publish(str(temperature))


my_dum_NLU = NLU("NLU","m_NLU","m_ASR")
my_dum_NLU.start_client()
my_dum_NLU._loop_forever()

# while True:
#     temperature = read_from_imaginary_thermometer()
#     my_dum_NLU.publish(str(temperature))
#     time.sleep(10)