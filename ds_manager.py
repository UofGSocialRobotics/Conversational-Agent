import threading
import config
from ca_logging import log
from whiteboard import whiteboard
import time


class DSManager:
    """
    Server is the main point of contact for all web clients.
    For each new client, the server creates new dedicates services (NLU, DM, NLG)
    Server is also in charge to send back messages to specific clients  - using specific channels.
    """
    def __init__(self):

        self.name = "Dialog-System-Manager"
        log.info("%s: init" % self.name)
        self.clients_services = dict()
        self.timer_threads = dict()


    ####################################################################################################
    ##                                          General Methods                                       ##
    ####################################################################################################
    def publish_for_client(self, message, topic):
        pass

    ####################################################################################################
    ##                                Methods related to distant client                               ##
    ####################################################################################################

    def start_timer(self, client_id):
        timer = threading.Timer(config.CONNECTION_TIMEOUT, function=self.stop_services, args=(client_id,))
        timer.start()
        self.timer_threads[client_id] = timer

    def reset_timer(self, client_id):
        if client_id not in self.timer_threads.keys():
            log.warn("%s: client %s already stoped!" % self.name)
        else:
            self.timer_threads[client_id].cancel()
            self.start_timer(client_id)

    def treat_message_from_client(self, msg_txt, client_id):
        """
        Creates dedicated services for client on first connection, or just forward the message.
        :param msg: client's message
        """


        # On first connection, create dedicated NLU/DM/NLG and subscribe to new DM topic
        # and start timer to kill services if no activity
        if client_id not in self.clients_services.keys():
            if config.MSG_CONNECTION in msg_txt:
                self.subscribe_whiteboard(config.MSG_NLG+client_id)
                self.create_services(client_id)
                self.start_timer(client_id)
                confirm_connection_messsage = config.MSG_CONFIRM_CONNECTION
                self.publish_for_client(confirm_connection_messsage, config.MSG_SERVER_OUT+client_id)
            else: # tell client they were disconnected
                error_message = "ERROR, you were disconnected. Start session again by refreshing page."
                self.publish_for_client(error_message, config.MSG_SERVER_OUT+client_id)
        else:
            # if not a reconnection, forward message by posting on dedicated topic and reset timer
            if config.MSG_CONNECTION not in msg_txt:
                topic = config.MSG_SERVER_IN+client_id
                self.publish_whiteboard(msg_txt, topic)
            self.reset_timer(client_id)

    ####################################################################################################
    ##                                Methods related to local whiteboard                             ##
    ####################################################################################################
    def publish_whiteboard(self, message, topic):
        whiteboard.publish(message, topic)

    def on_whiteboard_message(self, message, topic):
        self.treat_message_from_module(message, topic)

    def subscribe_whiteboard(self, topic):
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

        # star services in dedicated threads
        for key, s in self.clients_services[client_id].items():
            s.start_service()

    def stop_services(self, client_id):
        log.info("Shuting down services for client %s" % client_id)
        for c in self.clients_services[client_id].values():
            c.stop_service()
            del c
        del self.clients_services[client_id]

    def stop_all_services(self):
        for client_id, service_dict in self.clients_services.items():
            for service in service_dict.values():
                service.stop_service()
            if client_id in self.timer_threads.keys():
                self.timer_threads[client_id].cancel()
            time.sleep(1)
            log.debug("in stop_all_services, thread(s) left:")
            log.debug(threading.enumerate())

    def treat_message_from_module(self, message, topic):
        client_id = topic.split("/")[-1]
        self.publish_for_client(message, config.MSG_SERVER_OUT+client_id)
