from ca_logging import log
import config
import argparse
import threading
import gui

def main():
    log.info("Starting system")

    if config.USING == config.BROKER:
        import server_using_broker
        log.info("Will use broker")
        server = server_using_broker.ServerUsingBroker()
    elif config.USING == config.WEBSOCKETS:
        log.info("Will use websockets")
        import server_using_websockets
        server = server_using_websockets.ServerUsingWebSockets()
    else:
        log.warning("Wrong server config")
        exit(0)

    server_thread = threading.Thread(target=server.start_service, name="server_thread")
    # server.start_service()
    server_thread.start()

    return server_thread, server



if __name__ == '__main__':

    argp = argparse.ArgumentParser()
    argp.add_argument("--food", help="Movie recommendation system", action="store_true")
    argp.add_argument("--movies", help="Food recommendation system", action="store_true")
    # argp.add_argument("--debug", help="Sentence to debug", action="store")

    args = argp.parse_args()

    if args.movies:
        config.modules.set_domain("movies")
    elif args.food:
        config.modules.set_domain("food")
    else:
        argp.print_help()
        exit(0)

    server_thread, server = main()

    main_gui = gui.GUI(server, server_thread)
    main_gui.start_gui()

