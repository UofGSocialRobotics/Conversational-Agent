import config
from whiteboard import whiteboard
from ca_logging import log
import logging
import argparse
from termcolor import colored, cprint
import datetime
import time
import traceback
import random

class TestCora():
    def __init__(self, timeit, autotest_script=None):
        self.name = "TestCora"
        self.autotest_script = autotest_script
        self.autotest_script_index = 0
        self.timeit = timeit

        self.client_id = "test" + datetime.datetime.now().__str__()
        self.create_services()
        self.use_local_DB_bool = False

    def set_use_local_DB_value(self, val):
        self.use_local_DB_bool = val
        for service in self.services:
            if "DM" in service.name:
                service.set_use_local_recipe_DB(val)

    def start_testCora(self):
        bool_continue = True
        if not self.autotest_script:
            print(colored("####################################################################################################","yellow"))
            print(colored("You are about to test the full Cora-system (server side).\n","yellow"))
            print(colored("Because you're testing the server side, this test is LOCAL and nothing transits through firebase.","yellow"))
            print(colored("Note that the data corresponding to this test is still be saved locally by the DataCollector module.\n","yellow"))
            if self.use_local_DB_bool:
                utterance = input(colored("/!\\/!\\/!\\ We'll be using the local recipe DB --> queries to the local DB are NOT personalized with the user's preferences.\nAre you OK with that? (y: yes, q: no, cancel and quit): ", "yellow"))
                if utterance == "q":
                    self.quit()
                    bool_continue = False
                else:
                    print(colored("Nice!","yellow"))
            if bool_continue:
                print(colored("Enjoy your interaction with Cora!","yellow"))
                print(colored("####################################################################################################","yellow"))
        if not self.autotest_script or bool_continue:
            self.subscribe_whiteboard(config.MSG_NLG + self.client_id)
            self.subscribe_whiteboard(config.MSG_DATACOL_OUT + self.client_id)
            self.timer_response_time = None
            self.next_input()

    def create_services(self):
        self.services = list()
        for module_config in config.modules.modules:
            args = list(module_config.values())[2:]
            args.append(self.timeit)
            # print(*args)
            new_module = module_config["module"](self.client_id, *args)
            self.services.append(new_module)

        # star services in dedicated threads
        for s in self.services:
            s.start_service()


    def publish_whiteboard(self, message, topic):
        whiteboard.publish(message, topic)

    def on_whiteboard_message(self, message, topic):
        if config.MSG_NLG in topic:
            # self.publish_for_client(message, self.client_id, firebase_key=config.FIREBASE_KEY_DIALOG)
            print("Response time: %.3f sec" % (time.time() - self.timer_response_time))
            print(colored("Cora says: "+message["sentence"], "red"))
            self.publish_whiteboard({"dialog": message["sentence"]}, config.MSG_DATACOL_IN + self.client_id)
            if message["intent"] == "bye":
                self.quit()
            else:
                self.next_input()
        else:
            log.critical("Not implemented yet")

    def subscribe_whiteboard(self, topic):
        log.debug("%s subscribing to %s" %(self.name, topic))
        whiteboard.subscribe(subscriber=self, topic=topic)


    def next_input(self):
        if self.autotest_script:
            utterance = self.autotest_script[self.autotest_script_index]
            self.autotest_script_index += 1
            self.publish_whiteboard({"dialog": utterance}, config.MSG_DATACOL_IN + self.client_id)
            print(colored("User: "+utterance, "yellow"))
        else:
            utterance = input(colored("Enter text (q to quit): ","yellow"))
            if utterance == 'q':
                self.quit()
        topic = config.MSG_SERVER_IN + self.client_id
        self.timer_response_time = time.time()
        whiteboard.publish(utterance, topic)

    def quit(self):
        for c in self.services:
            c.stop_service()
        # exit(0)




if __name__ == "__main__":

    argp = argparse.ArgumentParser()
    argp.add_argument('domain', metavar='domain', type=str, help='Domain to test (e.g. movies? food?)')
    argp.add_argument("--autotest", help="To test the system with a predefined script (to write bellow directly in the python file)", action="store_true")
    argp.add_argument("--randomtest", help="To test the system with random utterances (chosen from list written in this file)", action="store_true")
    argp.add_argument("--test", help="To test the NLU module yourself", action="store_true")
    argp.add_argument("--logs", help="If you want to see the python logs in the console", action="store_true")
    argp.add_argument("--localDB", help="If you want avoid querying Spoonacular and use the limited local recipe DB instead", action="store_true")
    argp.add_argument("--timeit", help="If you want get the execution time for each module", action="store_true")

    hi = ["hi", "hello", "good morning", "hiya", "hallo"]
    i_am_emotion = ["i m tired", "good", "amazing", "i feel great", "OK", "fine", "i m good", "exhausted", "i had a good night and i feel great this morning!", "not good", "i feel bad", "i am in a bad mood", "i am sick", "I have a headache"]
    hungriness = ["i am starving", "i am hungry", "super hungry", "something light", "not too hungry", "never hungry for diner"]
    healthiness = ["very healthy", "i don t care", "i don t know", "healthy maybe?", "not healthy", "testy, not healthy", "no healthy i want pizza"]
    diet = ["no", "i am vegan", "i don t eat meat", "i dont eat dairy", "i eat gluten free", "no gluten please", "i don t eat eggs", "I am intolerant to shellfish", "no", "no", "no", "no", "no", "no", "no", "no"]
    time_options = ["I have time", "I don t have time", "I am in a rush", "something quick", "I have plenty of time", "not in a rush"]
    accept_recipe = ["no", "something else", "not that", "seems good", "yes", "sure", "I don t like salmon", "i don t like salad", "i don t like chicken"]
    conversation_stages = [hi, i_am_emotion, hungriness, healthiness, diet, time_options, accept_recipe]


    autotest_scripts = dict()
    # autotest_scripts["understand_yes_when_no"] = ["hello", "good and u?", " I ll be hungry, i m always hungry for dinner", "the healthier the better" , "nop", "I have time", " i have fish in the fridge that s going to go bad if i don t cook it today", "no, i don t like apples", "okay", "no thanks"]
    # autotest_scripts["always_says_no"] = ["hello", "good and u?", " I ll be hungry, i m always hungry for dinner", "the healthier the better" , "nop", "I have time", " i don t like salmon", "no", "anything else?", "no", "no"]
    # autotest_scripts["cant_find_recipes"] = ["hello", "good", "hungry", "very healthy" , "vegan", "quick", "oysters", "okay", "no"]
    # autotest_scripts["light_vegetarian_healty_notime_beans"] = ["hello", "Not so good", "light, I m not hungry", "might as well be good...", "I'm a vegeratian", "I don t feel like cooking", "beans", "no, not that", "no, not that either.", "ok", "sure", "thanks"]
    # autotest_scripts["hungry_notdiet_nothealty_time_chicken"] = ["hello", "Good", "Oh I'm really starving!", "I don t care a all.", "no", "I have plenty of time", "chicken", "no, not that", "no, not that either.", "no", "ok", "sure", "thanks"]
    # autotest_scripts["hungry_nodiet_healthy_notime_carrots"] = ["hello", "Great", "I m super hungry", "Yeah healthy is better obviously", "No special diet", "I am in a rush", "carrots", "OK", "nop"]
    # autotest_scripts["hungry_nococonut_nothealthy_time_parsnip"] = ["hello", "I've been better", "I m not on a diet and i m hungry", "I don t care", "I don t like coconut", "I have time", "parsnip", "why not", "sure", "thanks"]
    # autotest_scripts["recommend_squid_to_vegan"] = ["hello", "i had a good night and i feel great this morning!", " not too hungry", "testy, not healthy", "i am vegan", "I have plenty of time", "no", "no", "no", "no", "yes", "thanks"]
    autotest_scripts["error_pop_from_empty_list"] = ["hiya", "Lucile", "exhausted", "I live in Paris", "I depends, pasta most of the time.", "i am hungry", "very healthy", 'i dont eat dairy', "I have pabout 20 min", "Not that, i don t like fish", "OK", "sure", "something else", "no", "no", "no"]

    args = argp.parse_args()
    timeit = args.timeit if args.timeit else False
    if not args.logs:
        log.setLevel(logging.CRITICAL)

    try:
        test = None
        if(args.domain in ["movies", "food"]):
            config.modules.set_domain(args.domain)
            if args.autotest and autotest_scripts:
                for script_name, script in autotest_scripts.items():
                    print(colored(script_name, "blue"))
                    test = TestCora(timeit, script)
                    test.set_use_local_DB_value(args.localDB)
                    test.start_testCora()

            elif args.test:
                test = TestCora(timeit)
                test.set_use_local_DB_value(args.localDB)
                test.start_testCora()

            elif args.randomtest:
                script = list()
                for elt in conversation_stages:
                    script.append(random.choice(elt))
                for i in range(10):
                    script.append(random.choice(conversation_stages[-1]))
                test = TestCora(timeit, script)
                test.set_use_local_DB_value(args.localDB)
                test.start_testCora()

            else:
                args.print_help()
        else:
            argp.print_help()

    except:
        if test:
            test.quit()
        exceptiondata = traceback.format_exc().splitlines()
        print(exceptiondata[0])
        print("  [...]")
        # for line in exceptiondata[-9:]:
        for line in exceptiondata:
            print(line)


