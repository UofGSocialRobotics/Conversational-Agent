from simple_websocket_server import WebSocketServer, WebSocket
import ds_manager
import threading
import traceback
from ca_logging import log
import helper_functions as helper
import config
import time

class SimpleEcho(WebSocket):
    def handle(self):
        # echo message back to client
        self.send_message(self.data)

    def connected(self):
        print(self.address, 'connected')

    def handle_close(self):
        print(self.address, 'closed')



class DSManagerUsingWebsockets(WebSocket, ds_manager.DSManager):

    def handle(self):
        # echo message back to client
        # self.send_message(self.data)
        # print(self.data)
        # print(id)
        if not hasattr(self, 'client_id'):
            self.client_id = helper.random_id()
        self.treat_message_from_client(self.data, self.client_id)

    def publish_for_client(self, message, topic):
        self.send_message(message)

    def connected(self):
        log.info(self.address.__str__() + ' connected')
        self.send_message(config.MSG_CONFIRM_CONNECTION)
        ds_manager.DSManager.__init__(self)

    def handle_close(self):
        # traceback.print_exc()
        log.info(self.address + ' closed')

    def close(self, status=1000, reason=u''):
        self.stop_services(self.client_id)
        # WebSocket.close(self)



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
