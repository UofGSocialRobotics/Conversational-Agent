from simple_websocket_server import WebSocketServer, WebSocket
import ds_manager
# import threading
import traceback

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
        self.treat_message_from_client(self.data, "qwerty")

    def publish_for_client(self, message, topic):
        self.send_message(message)

    def connected(self):
        print(self.address, 'connected')
        self.send_message("Thanks for reaching out")
        ds_manager.DSManager.__init__(self)

    def handle_close(self):
        traceback.print_exc()
        print(self.address, 'closed')


class ServerUsingWebSockets:
    def start_service(self):
        print("here")
        server = WebSocketServer('localhost', 9000, DSManagerUsingWebsockets)
        # # print("here2")
        # t = threading.Thread(target=server.serve_forever)
        # print("here3")
        # t.start()
        server.serve_forever()
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            server.quit()
        print("here4")
        # server.serve_forever()


