import whiteboard
import server

my_whiteboard = whiteboard.Whiteboard()

my_server = server.Server(name="main_server", whiteboard=my_whiteboard)
my_server.start_service()

