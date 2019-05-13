import broker_client as bc
import dum_DM as dm
import dum_NLU as nlu
import threading
import broker_config as config

# service is a instance of a Client_Dialog_System or inherited class.
def start_service(service):
    # print("Creating new service in dedicated thread. Service name: %s"%(service.name))
    service.start_client_and_loop_forver()

def shut_down(clients_dict,threads_dict,client_id):
    print("Shuting down services for client %s"%(client_id))
    for c in clients_dict[client_id].values():
        c.disconnect()
        del c
    for t in threads_dict[client_id].values():
        t.join()

class Server(bc.Client_Dialog_System):
    '''
    Server is the main point of contact for all web clients.
    For each new client, the server creates new dedicates services (NLU, DM, NLG)
    Server is also in charge to send back messages to specific clients  - using specific channels.
    '''
    def __init__(self,name,msg_subscribe_type):
        bc.Client_Dialog_System.__init__(self,name,msg_subscribe_type)
        self.clients = dict()
        self.client_threads = dict()
        self.timer_threads = dict()

    def create_services(self,client_id):
        self.clients[client_id] = dict()
        self.client_threads[client_id] = dict()
        # create dedicated NLU
        new_nlu = nlu.NLU("NLU"+client_id,config.MSG_SERVER_IN+client_id,config.MSG_NLU+client_id)
        self.clients[client_id]["nlu"] = new_nlu
        # create dedicated DM
        new_dm = dm.DM("DM"+client_id,config.MSG_NLU+client_id,config.MSG_DM+client_id)
        self.clients[client_id]["dm"] = new_dm

        # star services in dedicated threads
        for key,s in self.clients[client_id].items():
            # print(s.name)
            t = threading.Thread(target=start_service, args=(s,))
            self.client_threads[client_id][key] = t
            t.start()
            # time.sleep(0.1)
            # print("After sleep")


    def treat_msg(self,msg):
        #identify sender
        if config.MSG_DM in msg.topic:
            self.treat_msg_from_module(msg)
        else:
            self.treat_msg_from_client(msg)

    def treat_msg_from_module(self,msg):
        t = str(msg.topic)
        client_id = t.split("/")[-1]
        print(" treat_msg_from_module")
        print(client_id)
        self.publish(str(msg.payload.decode('utf-8')),config.MSG_SERVER_OUT+client_id)

    def start_timer(self,client_id):
        timer = threading.Timer(config.CONNECTION_TIMEOUT, function=shut_down,args=(self.clients,self.client_threads,client_id))
        timer.start()
        self.timer_threads[client_id] = timer

    def reset_timer(self,client_id):
        if client_id not in self.client_threads.keys():
            print("%s ERR: client %s already stoped!")
        else:
            self.client_threads[client_id].cancel()
            self.start_timer(client_id)


    def treat_msg_from_client(self,msg):
        # get client ID
        msg_full = str(msg.payload.decode('utf-8'))
        msg_split = msg_full.split(':')
        client_id = msg_split[0]
        msg_split.pop(0)
        msg_txt = ':'.join(msg_split)

        # On first connection, create dedicated NLU/DM/NLG and subscribe to new DM topic
        # and start timer to kill services if no activity
        if client_id not in self.clients.keys():
            self.subscribe(config.MSG_DM+client_id)
            self.create_services(client_id)
            self.start_timer(client_id)

        else:
            # forward message by posting on dedicated topic
            self.publish(msg_txt,topic=config.MSG_SERVER_IN+client_id)
            self.reset_timer(client_id)


        # (cancel and) start timer to kill thread after time elapased.

if __name__ == "__main__":
    my_server = Server("main_server",config.MSG_CLIENT)
    my_server.start_client_and_loop_forver()
    # my_server.loop_forever()
