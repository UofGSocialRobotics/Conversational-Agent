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
    argp.add_argument("--food", help="Movie recommandation system", action="store_true")
    argp.add_argument("--movies", help="Food derommandation system", action="store_true")
    # argp.add_argument("--debug", help="Sentence to debug", action="store")

    args = argp.parse_args()

    if args.movies:
        import movies.movie_config as movie_config
        config.NLU = movie_config.NLU
        config.DM = movie_config.DM
        config.NLG = movie_config.NLG
        config.SentimentAnalysis = movie_config.SentimentAnalysis
        main()

