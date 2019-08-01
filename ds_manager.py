import threading
import config
from ca_logging import log
from whiteboard import whiteboard
import time
import json
import config_data_collection
import helper_functions as helper

class DSManager:
    """
    Server is the main point of contact for all web clients.
    For each new client, the server creates new dedicates services (NLU, DM, NLG)
    Server is also in charge to send back messages to specific clients  - using specific channels.
    """
    """Singleton class"""
    __instance = None

    @staticmethod
    def getInstance():
        """
        :return: the unique ClientsIDsStorage object
        """
        if DSManager.__instance == None:
            DSManager()
        return  DSManager.__instance


    def __init__(self):
        if DSManager.__instance != None:
            # log.error("Singleton Class: contructor should not be called. Use ClientsIDsStorage.getInstance()")
            log.debug("Calling constructor of DSManager")
            print(self.clients_services)
        else:
            DSManager.__instance = self
            self.name = "Dialog-System-Manager"
            log.info("%s: init" % self.name)
            self.clients_services = dict()
            self.timer_threads = dict()
            self.clients_websockets = dict()
            self.ws_timer_threads = dict()
            self.shut_down = False


    ####################################################################################################
    ##                                          General Methods                                       ##
    ####################################################################################################

    def create_message(self, content, msg_type):
        d = {'content': content, 'type':msg_type}
        json_string = json.dumps(d)
        return json_string

    def publish_for_client(self, message, topic, client_id = None):
        if config.USING == config.BROKER:
            log.error("%s: When not using websockets, this method should have been redefined in child class!" % self.name)
            raise NotImplementedError("%s: When not using websockets, this method should have been redefined in child class!" % self.name)
        else:
            if client_id in self.clients_websockets.keys():
                for ws in self.clients_websockets[client_id]:
                    ws.publish_for_client(message, topic, client_id)
            else:
                log.error("%s, publish_for_client: no websocket for client %s" % (self.name, client_id))

    ####################################################################################################
    ##                                Methods related to distant client                               ##
    ####################################################################################################

    def start_timer(self, client_id):
        timer = threading.Timer(config.CONNECTION_TIMEOUT, function=self.stop_services, args=(client_id,))
        timer.name = client_id
        timer.start()
        self.timer_threads[client_id] = timer

    def reset_timer(self, client_id):
        if client_id not in self.timer_threads.keys():
            log.warn("%s: client is already stoped!" % self.name)
        else:
            self.timer_threads[client_id].cancel()
            self.start_timer(client_id)


    def treat_message_from_client(self, msg_txt, client_id):
        t = threading.Thread(name="msg_client_"+client_id, target=self.thread_treat_message_from_client, args=(msg_txt, client_id))
        # t.setDaemon(True)
        t.start()


    def thread_treat_message_from_client(self, json_string, client_id):
        """
        Creates dedicated services for client on first connection, or just forwards the message.
        :param msg: client's message
        """

        json_msg = json.loads(json_string)
        log.debug(json_msg)
        content = json_msg['content']
        msg_type = json_msg['type']


        # On first connection, create dedicated NLU/DM/NLG and subscribe to new DM topic
        # and start timer to kill services if no activity
        if client_id not in self.clients_services.keys():
            log.debug("%s: new client" % self.name)
            if config.MSG_CONNECTION in content:
                self.subscribe_whiteboard(config.MSG_NLG + client_id)
                self.subscribe_whiteboard(config.MSG_AMTINFO_OUT + client_id)
                self.create_services(client_id)
                self.start_timer(client_id)
                confirm_connection_message = config.MSG_CONFIRM_CONNECTION
                self.publish_for_client(confirm_connection_message, config.MSG_SERVER_OUT + client_id, client_id)
            else: # tell client they were disconnected
                error_message = "ERROR, you were disconnected. Start session again by refreshing page."
                self.publish_for_client(error_message, config.MSG_SERVER_OUT + client_id, client_id)
        else:
            log.debug("%s: client already registered" % self.name)
            # if not a reconnection, forward message by posting on dedicated topic and reset timer
            if msg_type == config.MSG_TYPES_DATACOLLECTION:
                # json_msg = json.loads(msg_txt)
                topic = config.MSG_AMTINFO_IN + client_id
                self.publish_whiteboard(content, topic)
            elif msg_type == config.MSG_TYPES_DIALOG:
                # DIalog: send to data_collector module to save
                topic = config.MSG_AMTINFO_IN + client_id
                self.publish_whiteboard({config_data_collection.DIALOG: content}, topic)
                # distribute to NLU
                topic = config.MSG_SERVER_IN + client_id
                self.publish_whiteboard(content, topic)
            elif msg_type == config.MSG_TYPES_INFO and config.MSG_CONNECTION in content:
                # client reconnected after navigating on the website
                confirm_connection_message = config.MSG_CONFIRM_CONNECTION
                self.publish_for_client(confirm_connection_message, config.MSG_SERVER_OUT + client_id, client_id)
            else:
                log.warning("ds_manager: ERROR do not know what to do with client's message!!!")
            self.reset_timer(client_id)

    ####################################################################################################
    ##                                Methods related to local whiteboard                             ##
    ####################################################################################################
    def publish_whiteboard(self, message, topic):
        whiteboard.publish(message, topic)

    def on_whiteboard_message(self, message, topic):
        self.treat_message_from_module(message, topic)

    def subscribe_whiteboard(self, topic):
        log.debug("%s subsdribing to %s" %(self.name, topic))
        whiteboard.subscribe(subscriber=self, topic=topic)

    ####################################################################################################
    ##                                Methods related to local services                               ##
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
        # create dedicated AMT_info module
        new_datacollector = config.modules.DataCollector(subscribes=config.DataCollector_subscribes, publishes=config.DataCollector_publishes, clientid=client_id, ack_msg=config.MSG_AMTINFO_ACK)
        self.clients_services[client_id]["datacollector"] = new_datacollector

        # star services in dedicated threads
        for key, s in self.clients_services[client_id].items():
            s.start_service()

        self.publish_whiteboard({config_data_collection.CLIENT_ID: client_id}, config.MSG_AMTINFO_IN+client_id)

    def stop_services(self, client_id):
        log.info("Shuting down services for client %s" % client_id)
        if client_id in self.clients_services.keys():
            for c in self.clients_services[client_id].values():
                c.stop_service()
                del c
            del self.clients_services[client_id]
        if client_id in self.timer_threads.keys():
            self.timer_threads[client_id].cancel()

    def stop_all_services(self):
        self.shut_down = True
        for client_id, service_dict in self.clients_services.items():
            for service in service_dict.values():
                service.stop_service()
            if client_id in self.timer_threads.keys():
                self.timer_threads[client_id].cancel()
            if client_id in self.ws_timer_threads.keys():
                # print(self.ws_timer_threads[client_id])
                for i,timer in enumerate(self.ws_timer_threads[client_id]):
                    # print(timer)
                    timer.cancel()
            time.sleep(0.1)
            log.debug("in stop_all_services, thread(s) left:")
            log.debug(threading.enumerate())

    def treat_message_from_module(self, message, topic):
        log.debug("%s: entering treat_message_from_module, topic %s" % (self.name, topic))
        client_id = topic.split("/")[-1]
        if isinstance(message, dict):
            message_text = json.dumps(message)
            # print("we have a dict")
        else:
            message_text = message
        log.debug("%s: halfway in treat_message_from_module, topic %s" % (self.name, topic))
        self.publish_for_client(message_text, config.MSG_SERVER_OUT + client_id, client_id)
        # publish conversation for data_collection
        if config.MSG_NLG in topic:
            self.publish_whiteboard({"dialog": message["sentence"]}, config.MSG_AMTINFO_IN + client_id)


    ####################################################################################################
    ##                                Methods for websocket implementation                            ##
    ####################################################################################################

    def add_websocket(self, client_id, websocket):
        if client_id not in self.clients_websockets.keys():
            self.clients_websockets[client_id] = [websocket]
        else:
            self.clients_websockets[client_id].append(websocket)
            log.debug("%s: adding a websocket for client %s" % (self.name, client_id))

    def remove_web_socket(self, client_id, websoket):
        if websoket in self.clients_websockets[client_id]:
            self.clients_websockets[client_id].remove(websoket)
            log.debug("ds_manager removed websocket for client %s" % client_id)
        if len(self.clients_websockets[client_id]) == 0:
            if not self.shut_down:
                timer = threading.Timer(config.CONNECTION_TIMEOUT, function=self.stop_services, args=(client_id,))
                timer.name = "ds/ws_" + client_id
                if client_id not in self.ws_timer_threads.keys():
                    self.ws_timer_threads[client_id] = list()
                self.ws_timer_threads[client_id].append(timer)
                timer.start()
                # print("just started a new timer. Timer list:")
                # print(self.ws_timer_threads[client_id])
                # print("new timer is")
                # print(timer)
                # self.stop_services(client_id)

