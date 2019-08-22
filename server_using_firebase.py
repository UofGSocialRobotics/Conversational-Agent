import pyrebase
import traceback
import config
import datetime
import threading
import time
from whiteboard import whiteboard
import config_data_collection
from ca_logging import log
import helper_functions as helper
import pyrebase_multiple_refs

####################################################################################################
##                                          Stream handlers                                       ##
####################################################################################################



def stream_handler_users_ref(message):
    if server.server_started == True:
        client_id = message["path"][1:]
        server.new_client(client_id)


def filter_client_id_data(message):
    data = message["data"]
    path = message["path"]
    if data:
        try:
            if config.FIREBASE_KEY_SOURCE in data.keys() and data[config.FIREBASE_KEY_SOURCE] == config.FIREBASE_VALUE_SOURCE_AGENT:
                return False, False
            if config.FIREBASE_KEY_CLIENTID in data.keys():
                client_id = data[config.FIREBASE_KEY_CLIENTID]
            else:
                first_key = next(iter(data))
                client_id = data[first_key][config.FIREBASE_KEY_CLIENTID]
            if client_id and client_id in server.clients_services:
                server.reset_timer(client_id)
                return client_id, data
            else:
                return False, False
        except KeyError as e:
            log.warn("No client_id key")
    return False, False

def stream_handler_datacollection_ref(message):
    client_id, data = filter_client_id_data(message)
    if client_id:
        topic = config.MSG_DATACOL_IN + client_id
        whiteboard.publish(data, topic)


def stream_handler_dialog_ref(message):
    client_id, data = filter_client_id_data(message)
    if client_id:
        topic = config.MSG_DATACOL_IN + client_id
        # publish for data collection
        utterance = data[config.FIREBASE_KEY_TEXT]
        whiteboard.publish({config_data_collection.DIALOG: utterance}, topic)
        # distribute to NLU
        topic = config.MSG_SERVER_IN + client_id
        whiteboard.publish(utterance, topic)

def get_path_in_sessions(client_id, key=None):
    if key:
        return config.FIREBASE_KEY_SESSIONS + '/' + client_id + '/' + key
    else:
        return config.FIREBASE_KEY_SESSIONS + '/' + client_id


class ServerUsingFirebase:
    """Singleton class"""
    __instance = None

    @staticmethod
    def getInstance():
        """
        :return: the unique ServerUsingFirebase object
        """
        if ServerUsingFirebase.__instance == None:
            ServerUsingFirebase()
        return ServerUsingFirebase.__instance


    def __init__(self):
        if ServerUsingFirebase.__instance != None:
            log.debug("Calling constructor of ServerUsingFirebase")
        else:
            ServerUsingFirebase.__instance = self
            log.warn("THIS MESSAGE SHOULD APPEAR ONLY ONCE...")

            self.name = "Server"
            self.clients_services = dict()
            self.clients_threads = dict()
            self.timer_threads = dict()
            self.server_started = False

            self.firebase_root_ref = pyrebase_multiple_refs.PyrebaseMultipleRefs()
            self.firebase_users_ref = self.firebase_root_ref.new_ref(config.FIREBASE_KEY_USERS)
            self.firebase_streams_users = None
            self.firebase_streams_dialog = dict()
            self.firebase_streams_datacol = dict()



    ####################################################################################################
    ##                                          General Methods                                       ##
    ####################################################################################################

    # @overrides(ds_manager.DSManager)
    def start_service(self):
        try:
            self.firebase_streams_users = self.firebase_users_ref.stream(stream_handler_users_ref, stream_id="stream_users")
            time.sleep(2)
            self.server_started = True
        except KeyboardInterrupt:
            self.quit()

    # @overrides(ds_manager.DSManager)
    def quit(self, gui_quit=False):
        self.stop_all_services()
        log.info("------------ QUIT ------------")
        if not gui_quit:
            exit(0)


    ####################################################################################################
    ##                                Methods related to firebase                                     ##
    ####################################################################################################

     # @overrides(ds_manager.DSManager)
    def publish_for_client(self, message, client_id, firebase_key):
        log.debug("In publish_for_client")
        if client_id in self.clients_services:
            # ref = self.firebase_db.child(config.FIREBASE_KEY_SESSIONS).child(client_id)
            if firebase_key == config.FIREBASE_KEY_DIALOG or firebase_key == config.FIREBASE_KEY_ACK:
                timestamp = datetime.datetime.now().__str__()
                if firebase_key == config.FIREBASE_KEY_DIALOG:
                    message[config.FIREBASE_KEY_DATETIME] = timestamp
                    message[config.FIREBASE_KEY_SOURCE] = config.FIREBASE_VALUE_SOURCE_AGENT
                    self.firebase_root_ref.push_at(message, path=get_path_in_sessions(client_id=client_id, key=firebase_key))
                else:
                    data = dict()
                    data[config.FIREBASE_KEY_ACK] = True
                    self.firebase_root_ref.update_at(data, path=get_path_in_sessions(client_id))
                helper.print_message(self.name, "published", message.__str__(), topic=firebase_key)
            else:
                log.error("Calling publish_for_client with firebase key %s. Was expecting topic %s or %s" % (firebase_key, config.FIREBASE_KEY_ACK, config.FIREBASE_KEY_DIALOG))
                self.quit()
        else:
            log.error("%s, publish_for_client: unknown client %s" % (self.name, client_id))

    ####################################################################################################
    ##                                          Timer methods                                         ##
    ####################################################################################################

    def start_timer(self, client_id):
        timer = threading.Timer(config.CONNECTION_TIMEOUT, function=self.stop_services, args=(client_id,))
        timer.name = client_id
        timer.start()
        self.timer_threads[client_id] = timer

    def reset_timer(self, client_id):
        if client_id not in self.timer_threads.keys():
            log.warn("%s: client is already stopped!" % self.name)
        else:
            self.timer_threads[client_id].cancel()
            self.start_timer(client_id)


    ####################################################################################################
    ##                                             New client                                         ##
    ####################################################################################################



    def new_client(self, client_id):
        """
        Creates dedicated services for client on first connection
        :param msg: client's message
        """

        log.debug("%s: new client, id = %s" % (self.name, client_id))
        # Listeners: for modules
        self.subscribe_whiteboard(config.MSG_NLG + client_id)
        self.subscribe_whiteboard(config.MSG_DATACOL_OUT + client_id)
        # Listener: for client
        dialog_ref = self.firebase_root_ref.new_ref(get_path_in_sessions(client_id, config.FIREBASE_KEY_DIALOG))
        datacol_ref = self.firebase_root_ref.new_ref(get_path_in_sessions(client_id, config.FIREBASE_KEY_DATACOLLECTION))
        print("datacol_ref.path()")
        print(datacol_ref.path)
        self.firebase_streams_dialog[client_id] = dialog_ref.stream(stream_handler_dialog_ref, stream_id=client_id+"dialog")
        self.firebase_streams_datacol[client_id] = datacol_ref.stream(stream_handler_datacollection_ref, stream_id=client_id+"dialog")
        # Create services
        self.create_services(client_id)
        self.start_timer(client_id)
        confirm_connection_message = config.MSG_ACK_CONNECTION
        self.publish_for_client(True, client_id, firebase_key=config.FIREBASE_KEY_ACK)


    ####################################################################################################
    ##                                Methods related to local whiteboard                             ##
    ####################################################################################################
    def publish_whiteboard(self, message, topic):
        whiteboard.publish(message, topic)

    def on_whiteboard_message(self, message, topic):
        client_id = topic.split("/")[-1]
        if config.MSG_DATACOL_OUT in topic:
            self.publish_for_client(message, client_id, firebase_key=config.FIREBASE_KEY_ACK)
        elif config.MSG_NLG in topic:
            self.publish_for_client(message, client_id, firebase_key=config.FIREBASE_KEY_DIALOG)
        else:
            log.critical("Not implemented yet")

    def subscribe_whiteboard(self, topic):
        log.debug("%s subsdribing to %s" %(self.name, topic))
        whiteboard.subscribe(subscriber=self, topic=topic)


    ####################################################################################################
    ##                                Methods related to local modules                                ##
    ####################################################################################################


    def create_services(self, client_id):
        self.clients_services[client_id] = dict()
        # create dedicated NLU
        new_nlu = config.modules.NLU(subscribes=config.NLU_subscribes, publishes=config.NLU_publishes, clientid=client_id)
        self.clients_services[client_id]["nlu"] = new_nlu
        # create dedicated sentiment analysis
        new_sa = config.modules.SentimentAnalysis(subscribes=config.SentimentAnalysis_subscribes, publishes=config.SentimentAnalysis_publishes, clientid=client_id)
        self.clients_services[client_id]["sa"] = new_sa
        # create dedicated DM
        new_dm = config.modules.DM(subscribes=config.DM_subscribes, publishes=config.DM_publishes, clientid=client_id)
        self.clients_services[client_id]["dm"] = new_dm
        # create dedicated NLG
        new_nlg = config.modules.NLG(subscribes=config.NLG_subscribes, publishes=config.NLG_publishes, clientid=client_id)
        self.clients_services[client_id]["nlg"] = new_nlg
        # create dedicated data collector module
        new_datacollector = config.modules.DataCollector(subscribes=config.DataCollector_subscribes, publishes=config.DataCollector_publishes, clientid=client_id, ack_msg=config.FIREBASE_KEY_ACK)
        self.clients_services[client_id]["datacollector"] = new_datacollector

        # star services in dedicated threads
        for key, s in self.clients_services[client_id].items():
            s.start_service()

        self.publish_whiteboard({config_data_collection.CLIENT_ID: client_id}, config.MSG_DATACOL_IN+client_id)



    def close_stream_for_client(self, client_id, streams_dict):
        if client_id in streams_dict.keys():
            try:
                streams_dict[client_id].close()
            except AttributeError as e:
                log.warn("AttributeError: %s. Not solved." % e)
            del streams_dict[client_id]


    def stop_services(self, client_id):
        log.info("Shuting down services for client %s" % client_id)
        if client_id in self.clients_services.keys():
            for c in self.clients_services[client_id].values():
                c.stop_service()
                del c
            del self.clients_services[client_id]
        if client_id in self.timer_threads.keys():
            self.timer_threads[client_id].cancel()
        self.close_stream_for_client(client_id, self.firebase_streams_dialog)
        self.close_stream_for_client(client_id, self.firebase_streams_datacol)

    def stop_all_services(self):
        for client_id, service_dict in self.clients_services.items():
            for service in service_dict.values():
                service.stop_service()
            if client_id in self.timer_threads.keys():
                self.timer_threads[client_id].cancel()
            time.sleep(0.1)
        self.firebase_streams_users.close()
        log.debug("in stop_all_services, thread(s) left:")
        log.debug(threading.enumerate())



server = ServerUsingFirebase.getInstance()
