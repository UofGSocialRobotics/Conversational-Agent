from ca_logging import log
import config

log.info("Starting system")

if config.USING == config.BROKER:
    import server_using_borker
    log.info("Will use broker")
    server = server_using_borker.ServerUsingBroker()
elif config.USING == config.WEBSOCKETS:
    log.info("Will use websockets")
    import server_using_websockets
    server = server_using_websockets.ServerUsingWebSockets()
else:
    log.warning("Wrong server config")
    exit(0)

server.start_service()

