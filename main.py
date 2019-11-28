from ca_logging import log
import config
import argparse
import threading
import config_modules

import server_using_firebase

def main():
    log.info("Starting system")


    log.info("This server is using firebase")
    import server_using_firebase
    server = server_using_firebase.ServerUsingFirebase.getInstance()


    server_thread = threading.Thread(target=server.start_service, name="server_thread")
    # server.start_service()
    server_thread.start()

    return server_thread, server



if __name__ == '__main__':

    argp = argparse.ArgumentParser()
    argp.add_argument("--food", help="Movie recommendation system", action="store_true")
    argp.add_argument("--movies", help="Food recommendation system", action="store_true")
    argp.add_argument("--gui", help="To get a GUI to stop the system", action="store_true")
    # argp.add_argument("--debug", help="Sentence to debug", action="store")

    args = argp.parse_args()

    if args.movies:
        config_modules.modules.set_domain("movies")
    elif args.food:
        config_modules.modules.set_domain("food")
    else:
        argp.print_help()
        exit(0)

    server_thread, server = main()

    if args.gui:
        import gui
        main_gui = gui.GUI(server, server_thread)
        main_gui.start_gui()

