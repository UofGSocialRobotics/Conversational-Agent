import broker_client as bc
import dum_DM as dm
import dum_NLU as nlu
import threading
import broker_config as config
import paho.mqtt.client as paho
import helper_functions as helper

# service is a instance of a Client_Dialog_System or inherited class.
def start_service(service):
    # print("Creating new service in dedicated thread. Service name: %s" % (service.name))
    service.start_service()

def stop_services(clients_dict, threads_dict, client_id):
    print("Shuting down services for client %s" % (client_id))
    for c in clients_dict[client_id].values():
        c.stop_service()
        del c
    del clients_dict[client_id]
    # print("print dict")
    # for key, value in clients_dict.items():
    #     print(key, value)
    for t in threads_dict[client_id].values():
        t.join()


class Server:
    '''
    Server is the main point of contact for all web clients.
    For each new client, the server creates new dedicates services (NLU, DM, NLG)
    Server is also in charge to send back messages to specific clients  - using specific channels.
    '''
    def __init__(self, name, local_broker):
        self.name = name
        self.local_broker = local_broker
        self.client = None
        print("%s: init" % self.name)
        self.clients = dict()
        self.client_threads = dict()
        self.timer_threads = dict()


    ####################################################################################################
    ##                                          General Methods                                       ##
    ####################################################################################################

    def start_service(self):
        self.connect_distant_broker()
        self.subscribe_distant_broker()
        self.client.loop_forever()


    # def treat_message(self, msg, topic):
    #     #identify sender
    #     if config.MSG_DM in msg.topic:
    #         self.treat_message_from_module(msg)
    #     else:
    #         self.treat_message_from_client(msg)

    ####################################################################################################
    ##                                Methods related to distant broker                               ##
    ####################################################################################################

    def on_message(self, client, userdata, msg):
        helper.print_message(self.name, "received", str(msg.payload), msg.topic)
        self.treat_message_from_client(msg)
        # print(msg.topic + " " + str(msg.qos) + " " + str(msg.payload))

    def on_publish(self, client, user_data, mid):  #keep function signature from paho
        print("%s pusblished msg, id = %s" % (self.name, str(mid)))

    def on_subscribe(self, client, userdata, mid, granted_qos): #keep function signature from paho
        print("%s: subscribed, %s, %s" % (self.name, str(mid), str(granted_qos)))

    def on_disconnect(client, userdata, rc):
        print("%s disconnecting." % self.name)

    def connect_distant_broker(self):
        if self.client:
            print("Already connected")
        else:
            self.client = paho.Client()
            self.client.on_publish = self.on_publish
            self.client.on_subscribe = self.on_subscribe
            self.client.on_message = self.on_message
            self.client.connect(config.ADDRESS, config.PORT)
            # self.client.loop_start()
            print("%s: connexion started"%self.name)

    def subscribe_distant_broker(self):
        topic = config.MSG_CLIENT
        print("%s: suscribing to %s" % (self.name, topic))
        self.client.subscribe(topic, qos=2)


    def publish_distant_broker(self, message, topic):
        helper.print_message(self.name, "publishing", message, topic)
        (rc, mid) = self.client.publish(topic, message, qos=2)

    ####################################################################################################
    ##                                Methods related to distant client                               ##
    ####################################################################################################

    def start_timer(self, client_id):
        timer = threading.Timer(config.CONNECTION_TIMEOUT, function=stop_services, args=(self.clients, self.client_threads, client_id))
        timer.start()
        self.timer_threads[client_id] = timer

    def reset_timer(self, client_id):
        if client_id not in self.timer_threads.keys():
            print("%s ERR: client %s already stoped!")
        else:
            self.timer_threads[client_id].cancel()
            self.start_timer(client_id)

    def treat_message_from_client(self, msg):
        # get client ID
        msg_full = str(msg.payload.decode('utf-8'))
        msg_split = msg_full.split(':')
        client_id = msg_split[0]
        msg_split.pop(0)
        msg_txt = ':'.join(msg_split)

        # On first connection, create dedicated NLU/DM/NLG and subscribe to new DM topic
        # and start timer to kill services if no activity
        if client_id not in self.clients.keys():
            print("server suscribing to "+config.MSG_DM+client_id)
            self.subscribe_local_broker(config.MSG_DM+client_id)
            self.create_services(client_id)
            self.start_timer(client_id)

        else:
            # if not a reconnection, forward message by posting on dedicated topic and reset timer
            if config.MSG_CONNECTION not in msg_txt:
                topic = config.MSG_SERVER_IN+client_id
                self.publish_local_broker(msg_txt, topic)
            self.reset_timer(client_id)

    ####################################################################################################
    ##                                Methods related to local broker                                 ##
    ####################################################################################################
    def publish_local_broker(self, message, topic):
        self.local_broker.publish(message, topic)

    def on_local_message(self, message, topic):
        self.treat_message_from_module(message, topic)

    def subscribe_local_broker(self, topic):
        self.local_broker.subscribe(subscriber=self, topic=topic)

    ####################################################################################################
    ##                                Methods related to local services                               ##
    ####################################################################################################


    def create_services(self, client_id):
        self.clients[client_id] = dict()
        self.client_threads[client_id] = dict()
        # create dedicated NLU
        new_nlu = nlu.NLU(name="NLU"+client_id, msg_subscribe_type=config.MSG_SERVER_IN+client_id, msg_publish_type=config.MSG_NLU+client_id, local_broker=self.local_broker)
        self.clients[client_id]["nlu"] = new_nlu
        # create dedicated DM
        new_dm = dm.DM(name="DM"+client_id, msg_subscribe_type=config.MSG_NLU+client_id, msg_publish_type=config.MSG_DM+client_id, local_broker=self.local_broker)
        self.clients[client_id]["dm"] = new_dm

        # star services in dedicated threads
        for key, s in self.clients[client_id].items():
            t = threading.Thread(target=start_service, args=(s, ))
            self.client_threads[client_id][key] = t
            t.start()

    def treat_message_from_module(self, message, topic):
        client_id = topic.split("/")[-1]
        self.publish_distant_broker(message, config.MSG_SERVER_OUT+client_id)
