from ca_logging import log
import config
import argparse

def main():
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


if __name__ == '__main__':

    argp = argparse.ArgumentParser()
    argp.add_argument("--food", help="Movie recommendation system", action="store_true")
    argp.add_argument("--movies", help="Food recommendation system", action="store_true")
    # argp.add_argument("--debug", help="Sentence to debug", action="store")

    args = argp.parse_args()

    if args.movies:
        config.modules.set_domain("movies")
        main()
    elif args.food:
        config.modules.set_domain("food")
        main()



