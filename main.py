import local_broker
import server

my_local_broker = local_broker.LocalBrocker()

my_server = server.Server(name="main_server", local_broker=my_local_broker)
my_server.start_service()

