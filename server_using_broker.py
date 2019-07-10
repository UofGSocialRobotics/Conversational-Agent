import threading
import config
import paho.mqtt.client as paho
import helper_functions as helper
import traceback
from ca_logging import log
import ds_manager


class ServerUsingBroker(paho.Client, ds_manager.DSManager):
    """
    Server is the main point of contact for all web clients.
    For each new client, the server creates new dedicates services (NLU, DM, NLG)
    Server is also in charge to send back messages to specific clients  - using specific channels.
    """
    def __init__(self):
        paho.Client.__init__(self)
        ds_manager.DSManager.__init__(self)


    ####################################################################################################
    ##                                          General Methods                                       ##
    ####################################################################################################

    # @overrides(ds_manager.DSManager)
    def start_service(self):
        self.connect_distant_broker()
        self.subscribe_distant_broker()
        try:
            self.loop_forever()
        except KeyboardInterrupt:
            self.quit()

    # @overrides(ds_manager.DSManager)
    def quit(self, gui_quit=False):
        self.stop_all_services()
        self.disconnect()
        log.info("------------ QUIT ------------")
        if not gui_quit:
            exit(0)

    ####################################################################################################
    ##                                Methods related to distant broker                               ##
    ####################################################################################################

    # @overrides(paho.Client)
    def on_message(self, client, userdata, msg):
        try:
            helper.print_message(self.name, "received", str(msg.payload), msg.topic)
            msg_text, client_id = self.extract_messagetext_and_clientid(msg)
            self.treat_message_from_client(msg_text, client_id)
        except:
            traceback.print_exc()
            self.quit()

    # @overrides(paho.Client)
    def on_publish(self, client, user_data, mid):  #keep function signature from paho
        log.info("%s pusblished msg, id = %s" % (self.name, str(mid)))

    # @override(paho.Client)
    def on_subscribe(self, client, userdata, mid, granted_qos): #keep function signature from paho
        log.info("%s: subscribed, %s, %s" % (self.name, str(mid), str(granted_qos)))

    # @overrides(paho.Client)
    def on_disconnect(self, client, userdata, rc):
        log.info("%s disconnecting." % self.name)

    def connect_distant_broker(self):
        # self.on_publish = self.on_publish
        # self.on_subscribe = self.on_subscribe
        # self.on_message = self.on_message
        # self.on_log = on_log
        self.connect(config.ADDRESS, config.PORT)
        # self.loop_start()
        log.info("%s: connexion started"%self.name)

    def subscribe_distant_broker(self):
        topic = config.MSG_CLIENT
        log.info("%s: subscribing to %s" % (self.name, topic))
        # method inherited from Paho client
        self.subscribe(topic, qos=2)

    # @overrides(ds_manager.DSManager)
    def publish_for_client(self, message, topic, client_id = None):
        helper.print_message(self.name, "publishing", message, topic)
        # method inherited from Paho client
        (rc, mid) = self.publish(topic, message, qos=2)



    def extract_messagetext_and_clientid(self, msg):

        # get client ID
        msg_full = str(msg.payload.decode('utf-8'))
        msg_split = msg_full.split(':')
        client_id = msg_split[0]
        msg_split.pop(0)
        msg_txt = ':'.join(msg_split)
        return msg_txt, client_id
