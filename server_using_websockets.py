from simple_websocket_server import WebSocketServer, WebSocket
import ds_manager
import threading
import traceback
from ca_logging import log
import helper_functions as helper
import config
import time
import config_data_collection
import json

def parse_message(json_string):
    json_msg = json.loads(json_string)
    client_id, msg_text = json_msg[config_data_collection.CLIENT_ID], json_msg[config_data_collection.MSG_TEXT]
    return client_id, msg_text


class SimpleEcho(WebSocket):
    def handle(self):
        # echo message back to client
        self.send_message(self.data)

    def connected(self):
        print(self.address, 'connected')

    def handle_close(self):
        print(self.address, 'closed')



class DSManagerUsingWebsockets(WebSocket):
    """
    Major problem with this implementation:
    One DSManager is created by each websocket. Each DS Manager creates their own services for the SAME client!
    """
    # def __init__(self):
    #     self.ds_manager = None
    #     self.client_id = None

    def handle(self):
        print("DSManagerUsingWebsockets enter handle")
        client_id, text = parse_message(self.data)
        print("Parsed json message:")
        print(client_id, text)

        if not hasattr(self, 'client_id'):
        # if not self.client_id:
            self.client_id = client_id
            self.ds_manager.add_websocket(client_id, self)
            print("we re now there")

        self.ds_manager.treat_message_from_client(text, client_id)
        print("DSManagerUsingWebsockets exit handle")

    def publish_for_client(self, message, topic, client_id):
        self.send_message(message)

    def connected(self):
        log.info(self.address.__str__() + ' connected')
        self.ds_manager = ds_manager.DSManager.getInstance()
        print("here")
        self.send_message(config.MSG_CONFIRM_CONNECTION)
        print("DSManagerUsingWebsockets exit connected")
        # ds_manager.DSManager.__init__(self)


    def handle_close(self):
        # traceback.print_exc()
        log.info(self.address + ' closed')

    def close(self, status=1000, reason=u''):
        # self.stop_services(self.client_id)
        WebSocket.close(self)
        # pass



class ServerUsingWebSockets:

    def serve_forever(self):
        while(self.in_service):
            self.server.handle_request()

    def start_service(self):
        self.server = WebSocketServer('localhost', 9000, DSManagerUsingWebsockets)
        self.in_service = True
        # t = threading.Thread(target=self.server.serve_forever)
        t = threading.Thread(target=self.serve_forever)
        try:
            t.start()
            log.info("WebSocket Server ready, waiting for connections. Running on localhost:9000.")
        except KeyboardInterrupt:
            traceback.print_exc()
            exit(0)

    def quit(self, gui_quit=False):
        self.in_service = False
        time.sleep(0.2)
        self.server.close()
        log.info("------------ QUIT ------------")
        if not gui_quit:
            exit(0)
