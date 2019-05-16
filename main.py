import server
from ca_logging import log

log.info("Starting system")


my_server = server.Server(name="main_server")
my_server.start_service()

