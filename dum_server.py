import broker_client as bc
import dum_DM as dm
import dum_NLU as nlu
import threading
import broker_config as config
import time

# service is a instance of a Client_Dialog_System or inherited class.
def start_service(service):
    # print("Creating new service in dedicated thread. Service name: %s"%(service.name))
    service.start_client_and_loop_forver()


class Server(bc.Client_Dialog_System):
    '''
    Server is the main point of contact for all web clients.
    For each new client, the server creates new dedicates services (NLU, DM, NLG)
    Server is also in charge to send back messages to specific clients  - using specific channels.
    '''
    def __init__(self,name,msg_subscribe_type):
        bc.Client_Dialog_System.__init__(self,name,msg_subscribe_type)
        self.clients = dict()

    def create_services(self,client_id):
        self.clients[client_id] = dict()
        # create dedicated NLU
        new_nlu = nlu.NLU("NLU"+client_id,config.MSG_SERVER_IN+client_id,config.MSG_NLU+client_id)
        self.clients[client_id]["nlu"] = new_nlu
        # create dedicated DM
        new_dm = dm.DM("DM"+client_id,config.MSG_NLU+client_id,config.MSG_DM+client_id)
        self.clients[client_id]["dm"] = new_dm

        # star services in dedicated threads
        for s in self.clients[client_id].values():
            # print(s.name)
            t = threading.Thread(target=start_service, args=(s,))
            t.start()
            # time.sleep(0.1)
            # print("After sleep")


    def _treat_msg(self,msg):
        #identify sender
        if config.MSG_DM in msg.topic:
            self._treat_msg_from_module(msg)
        else:
            self._treat_msg_from_client(msg)

    def _treat_msg_from_module(self,msg):
        t = str(msg.topic)
        client_id = t.split("/")[-1]
        print(" _treat_msg_from_module")
        print(client_id)
        self.publish(str(msg.payload.decode('utf-8')),config.MSG_SERVER_OUT+client_id)

    def _treat_msg_from_client(self,msg):
        # get client ID
        msg_full = str(msg.payload.decode('utf-8'))
        msg_split = msg_full.split(':')
        client_id = msg_split[0]
        msg_split.pop(0)
        msg_txt = ':'.join(msg_split)

        # On first connection, create dedicated NLU/DM/NLG that run on dedicated threads and subscribe to new
        if client_id not in self.clients.keys():
            self._subscribe(config.MSG_DM+client_id)
            self.create_services(client_id)

        else:
            # forward message by posting on dedicated topic
            self.publish(msg_txt,topic=config.MSG_SERVER_IN+client_id)

if __name__ == "__main__":
    my_server = Server("main_server",config.MSG_CLIENT)
    my_server.start_client_and_loop_forver()
    # my_server._loop_forever()
