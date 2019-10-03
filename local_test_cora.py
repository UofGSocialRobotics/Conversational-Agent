import config
from whiteboard import whiteboard
from ca_logging import log
import logging
import argparse
from termcolor import colored
import datetime

class TestCora():
    def __init__(self, autotest_script=None):
        self.services = dict()
        self.name = "TestCora"
        self.autotest_script = autotest_script
        self.autotest_script_index = 0
        self.client_id = "test" + datetime.datetime.now().__str__()
        print(colored("####################################################################################################","yellow"))
        print(colored("You are about to test the full Cora-system (server side).\n","yellow"))
        print(colored("Because you're testing the server side, this test is LOCAL and nothing transits through firebase.","yellow"))
        print(colored("Note that the data corresponding to this test is still saved locally by the DataCollector module.\n","yellow"))
        print(colored("Enjoy your interaction with Cora!","yellow"))
        print(colored("####################################################################################################","yellow"))
        self.create_services()
        self.subscribe_whiteboard(config.MSG_NLG + self.client_id)
        self.subscribe_whiteboard(config.MSG_DATACOL_OUT + self.client_id)
        self.next_input()

    def create_services(self):
        # create dedicated NLU
        client_id = self.client_id
        new_nlu = config.modules.NLU(subscribes=config.NLU_subscribes, publishes=config.NLU_publishes, clientid=client_id)
        self.services["nlu"] = new_nlu
        # create dedicated sentiment analysis
        new_sa = config.modules.SentimentAnalysis(subscribes=config.SentimentAnalysis_subscribes, publishes=config.SentimentAnalysis_publishes, clientid=client_id)
        self.services["sa"] = new_sa
        # create dedicated DM
        new_dm = config.modules.DM(subscribes=config.DM_subscribes, publishes=config.DM_publishes, clientid=client_id)
        self.services["dm"] = new_dm
        # create dedicated NLG
        new_nlg = config.modules.NLG(subscribes=config.NLG_subscribes, publishes=config.NLG_publishes, clientid=client_id)
        self.services["nlg"] = new_nlg
        # create dedicated data collector module
        new_datacollector = config.modules.DataCollector(subscribes=config.DataCollector_subscribes, publishes=config.DataCollector_publishes, clientid=client_id, ack_msg=config.FIREBASE_KEY_ACK)
        self.services["datacollector"] = new_datacollector

        # star services in dedicated threads
        for key, s in self.services.items():
            s.start_service()


    def publish_whiteboard(self, message, topic):
        whiteboard.publish(message, topic)

    def on_whiteboard_message(self, message, topic):
        if config.MSG_NLG in topic:
            # self.publish_for_client(message, self.client_id, firebase_key=config.FIREBASE_KEY_DIALOG)
            print(colored("Cora says: "+message["sentence"], "red"))
            if message["intent"] == "bye":
                self.quit()
            else:
                self.next_input()
        else:
            log.critical("Not implemented yet")

    def subscribe_whiteboard(self, topic):
        log.debug("%s subsdribing to %s" %(self.name, topic))
        whiteboard.subscribe(subscriber=self, topic=topic)


    def next_input(self):
        if self.autotest_script:
            utterance = self.autotest_script[self.autotest_script_index]
            self.autotest_script_index += 1
            print(colored("User: "+utterance, "yellow"))
        else:
            utterance = input(colored("Enter text (q to quit): ","yellow"))
            if utterance == 'q':
                self.quit()
        topic = config.MSG_SERVER_IN + self.client_id
        whiteboard.publish(utterance, topic)

    def quit(self):
        for c in self.services.values():
            c.stop_service()
        # exit(0)




if __name__ == "__main__":

    argp = argparse.ArgumentParser()
    argp.add_argument('domain', metavar='domain', type=str, help='Domain to test (e.g. movies? food?)')
    argp.add_argument("--autotest", help="To test the system with a predefined script (to write bellow directly in the python file)", action="store_true")
    argp.add_argument("--test", help="To test the NLU module yourself", action="store_true")
    argp.add_argument("--logs", help="If you want to see the python logs in the console", action="store_true")

    autotest_scripts = dict()
    autotest_scripts["light_vegetarian_healty_notime_beans"] = ["hello", "Not so good", "light, I m not hungry", "might as well be good...", "I'm a vegeratian", "I don t feel like cooking", "beans", "sure", "no thanks"]
    autotest_scripts["hungry_nodiet_healthy_notime_carrots"] = ["hello", "Great", "I m super hungry", "Yeah healthy is better obviously", "No special diet", "I am in a rush", "carrots", "OK", "nop"]
    autotest_scripts["hungry_nococonut_nothealthy_time_parsnip"] = ["hello", "I've been better", "I m not on a diet and i m hungry", "I don t care", "I don t like coconut", "I have time", "parsnip", "why not", "sure", "thanks"]

    args = argp.parse_args()
    if not args.logs:
        log.setLevel(logging.CRITICAL)

    if(args.domain in ["movies", "food"]):
        config.modules.set_domain(args.domain)
        if args.autotest and autotest_scripts:
            for script_name, script in autotest_scripts.items():
                print(colored(script_name, "blue"))
                test = TestCora(script)

        elif args.test:
            TestCora()
        else:
            args.print_help()
    else:
        argp.print_help()


