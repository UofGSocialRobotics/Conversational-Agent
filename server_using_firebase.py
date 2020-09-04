import config
import datetime
import threading
import time
from whiteboard import whiteboard
import config_data_collection
from ca_logging import log
import helper_functions as helper
import pyrebase_multiple_refs
import math
from termcolor import colored
import config_modules

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
    # print(data, path)
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
        if config.FIREBASE_KEY_FOOD_DIAGNOSIS_ANSWERS in data.keys() and data[config.FIREBASE_KEY_FOOD_DIAGNOSIS_ANSWERS]:
            topic = config.MSG_HEALTH_DIAGNOSTIC_IN + client_id
            whiteboard.publish(data[config.FIREBASE_KEY_FOOD_DIAGNOSIS_ANSWERS], topic)


def stream_handler_dialog_ref(message):
    client_id, data = filter_client_id_data(message)
    if client_id:
        topic = config.MSG_DATACOL_IN + client_id
        if config.FIREBASE_KEY_TEXT in data.keys():
            utterance = data[config.FIREBASE_KEY_TEXT]
        elif config.FIREBASE_LIKED_RECIPES in data.keys():
            utterance = data[config.FIREBASE_LIKED_RECIPES]
        # publish for data collection
        whiteboard.publish({config_data_collection.DIALOG: data}, topic)
        # distribute to NLU
        topic = config.MSG_SERVER_IN + client_id
        whiteboard.publish(utterance, topic)


def stream_handler_rsdata_ref(message):
    client_id, data = filter_client_id_data(message)
    if client_id:
        topic = config.MSG_RS_IN + client_id
        log.debug(message)
        whiteboard.publish(data, topic)


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
            self.n_clients = 0
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
        # log.debug("In publish_for_client")
        # log.debug("firebase key")
        # log.debug(firebase_key)
        if client_id in self.clients_services:
            # ref = self.firebase_db.child(config.FIREBASE_KEY_SESSIONS).child(client_id)
            if firebase_key == config.FIREBASE_KEY_DIALOG or firebase_key == config.FIREBASE_KEY_ACK or firebase_key == config.FIREBASE_KEY_XP_COND or firebase_key == config.FIREBASE_KEY_RECIPE:

                if firebase_key == config.FIREBASE_KEY_DIALOG:
                    message_to_send, sentences_and_delays = dict(), None
                    for key, value in message.items():
                        if key != 'sentences_and_delays':
                            message_to_send[key] = value
                        else:
                            sentences_and_delays = value
                    n_messages_to_send = len(sentences_and_delays)
                    for i, elt in enumerate(sentences_and_delays):
                        sentence, delay = elt['sentence'], elt['delay']
                        if delay:
                            time.sleep(delay)
                        message_to_send['sentence'] = sentence
                        message_to_send['delay'] = delay
                        message_to_send['wait_for_more'] = True if i < (n_messages_to_send - 1) else False
                        timestamp = datetime.datetime.now().__str__()
                        message_to_send[config.FIREBASE_KEY_DATETIME] = timestamp
                        message_to_send[config.FIREBASE_KEY_SOURCE] = config.FIREBASE_VALUE_SOURCE_AGENT
                        # if message_to_send['food_recipe']:
                        #     message_to_send['rid'] = message_to_send['food_recipe']['id']
                        # message_to_send['food_recipe'] = None

                        # if 'utilities' in message_to_send.keys():
                        #     message_to_send['utilities'] = None
                        # if 'cf_scores' in message_to_send.keys():
                        #     message_to_send['cf_scores'] = None
                        # if 'relaxed_constraints' in message_to_send.keys():
                        #     message_to_send['relaxed_constraints'] = None

                        print(colored(message_to_send, 'blue'))
                        print(type(message_to_send))
                        self.firebase_root_ref.push_at(message_to_send, path=get_path_in_sessions(client_id=client_id, key=firebase_key))
                        # if 'recipe_card' in message_to_send and message_to_send['recipe_card']:
                        #     self.firebase_root_ref.put_here(message_to_send['recipe_card'])
                        #     print(colored("trying to push card", 'red'))
                        # publish for data collection
                        topic = config.MSG_DATACOL_IN + client_id
                        for_data_col = dict()
                        for_data_col[config_data_collection.DIALOG] = message_to_send
                        whiteboard.publish(message=for_data_col, topic=topic)

                elif firebase_key == config.FIREBASE_KEY_RECIPE:
                    timestamp = datetime.datetime.now().__str__()
                    message_to_send = message
                    message_to_send[config.FIREBASE_KEY_DATETIME] = timestamp
                    message_to_send[config.FIREBASE_KEY_SOURCE] = config.FIREBASE_VALUE_SOURCE_AGENT
                    self.firebase_root_ref.push_at(message_to_send, path=get_path_in_sessions(client_id=client_id, key=config.FIREBASE_KEY_DIALOG))
                    # publish for data collection
                    topic = config.MSG_DATACOL_IN + client_id
                    for_data_col = dict()
                    for_data_col[config_data_collection.DIALOG] = message_to_send
                    whiteboard.publish(message=for_data_col, topic=topic)

                elif firebase_key == config.FIREBASE_KEY_XP_COND or (isinstance(message, dict) and (config.FIREBASE_KEY_DATA_RECO in message.keys() or config.FIREBASE_KEY_RS_EVAL_DATA in message.keys())):
                    self.firebase_root_ref.update_at(message, path=get_path_in_sessions(client_id))

                else:
                    data = dict()
                    data[config.FIREBASE_KEY_ACK] = True
                    self.firebase_root_ref.update_at(data, path=get_path_in_sessions(client_id))
                helper.print_message(self.name, "published", message, topic=firebase_key)
            else:
                log.error("Calling publish_for_client with firebase key %s. Was expecting topic %s, %s or %s" % (firebase_key, config.FIREBASE_KEY_ACK, config.FIREBASE_KEY_DIALOG, config.FIREBASE_KEY_RECIPE))
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
            log.warn("%s: client %s  is already stopped!" % (self.name, client_id))
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
        if config.DOMAIN == config.DOMAIN_RS_EVAL:
            self.subscribe_whiteboard(config.MSG_RS_OUT + client_id)
        else:
            self.subscribe_whiteboard(config.MSG_NLG + client_id)
        self.subscribe_whiteboard(config.MSG_DATACOL_OUT + client_id)
        # Listener: for client
        dialog_ref = self.firebase_root_ref.new_ref(get_path_in_sessions(client_id, config.FIREBASE_KEY_DIALOG))
        datacol_ref = self.firebase_root_ref.new_ref(get_path_in_sessions(client_id, config.FIREBASE_KEY_DATACOLLECTION))
        rs_data_ref = self.firebase_root_ref.new_ref(get_path_in_sessions(client_id, config.FIREBASE_KEY_RS_DATA))
        self.firebase_streams_dialog[client_id] = dialog_ref.stream(stream_handler_dialog_ref, stream_id=client_id+"dialog")
        self.firebase_streams_datacol[client_id] = datacol_ref.stream(stream_handler_datacollection_ref, stream_id=client_id+"dialog")
        self.firebase_streams_dialog[client_id] = rs_data_ref.stream(stream_handler_rsdata_ref, stream_id=client_id+"RSdata")
        # Create services
        self.create_services(client_id)
        self.start_timer(client_id)
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
            # print(colored(message, 'blue'))
            self.publish_for_client(message, client_id, firebase_key=config.FIREBASE_KEY_DIALOG)
            if isinstance(message, dict) and "intent" in message.keys() and message["intent"] == "bye":
                self.publish_for_client(message, client_id, firebase_key=config.FIREBASE_KEY_ACK)
        elif config.MSG_RS_OUT in topic:
            self.publish_for_client(message, client_id, firebase_key=config.FIREBASE_KEY_RECIPE)
        else:
            log.critical("Not implemented yet")

    def subscribe_whiteboard(self, topic):
        log.debug("%s subsdribing to %s" %(self.name, topic))
        whiteboard.subscribe(subscriber=self, topic=topic)


    ####################################################################################################
    ##                                Methods related to local modules                                ##
    ####################################################################################################


    def create_services(self, client_id):
        self.clients_services[client_id] = list()
        for module_config in config_modules.modules.modules:
            args = list(module_config.values())[2:]
            # print(module_config)
            new_module_name = module_config["name"]
            if new_module_name == "NLG":
                if config.aamas_study_CS:
                    cs = config.possible_CS[self.n_clients % len(config.possible_CS)]
                    self.publish_for_client({config.FIREBASE_KEY_XP_COND: cs}, client_id, config.FIREBASE_KEY_XP_COND)
                    self.publish_whiteboard({config.FIREBASE_KEY_XP_COND: cs}, config.MSG_DATACOL_IN+client_id)
                    msg = "XP condition, cs = " + cs
                    print(colored(msg, "cyan"))
                    log.debug(msg)
                else:
                    cs = config.exp_cs_control
                args.append(cs)
            # print(module_config["module"])
            new_module = module_config["module"](client_id, *args)                
            
            self.clients_services[client_id].append(new_module)

        self.n_clients += 1
        for s in self.clients_services[client_id]:
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
        log.info("Shutting down services for client %s" % client_id)
        if client_id in self.clients_services.keys():
            for c in self.clients_services[client_id]:
                c.stop_service()
        if client_id in self.timer_threads.keys():
            self.timer_threads[client_id].cancel()
        self.close_stream_for_client(client_id, self.firebase_streams_dialog)
        self.close_stream_for_client(client_id, self.firebase_streams_datacol)

    def stop_all_services(self):
        log.debug("in stop_all_services, thread(s) left:")
        log.debug(threading.enumerate())
        for client_id, services_list in self.clients_services.items():
            # for service in service_dict.values():
            #     service.stop_service()
            self.stop_services(client_id)
            if client_id in self.timer_threads.keys():
                self.timer_threads[client_id].cancel()
            time.sleep(0.1)
        self.firebase_streams_users.close()
        log.debug("in stop_all_services, thread(s) left:")
        log.debug(threading.enumerate())



server = ServerUsingFirebase.getInstance()
