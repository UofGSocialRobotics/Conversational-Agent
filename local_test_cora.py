import config
import config_modules
from whiteboard import whiteboard
from ca_logging import log
import logging
import argparse
from termcolor import colored, cprint
import datetime
import time
import traceback
import random
import csv
import json
import pandas as pd

from food.resources.recipes_DB.allrecipes.nodejs_scrapper import consts

csv_path = "local_test.csv"

with open(consts.json_xUsers_Xrecipes_path, 'r') as fDB:
    recipes_data = json.load(fDB)['recipes_data']

def get_healthScore(rid):
    return recipes_data[rid]['FSAscore']

def get_avg_healthScore(rids_list):
    if not liked_recipes:
        return -1
    sum = 0
    for rid in rids_list:
        sum += get_healthScore(rid)
    return float(sum/len(rids_list))

csv_first_row = ['cf_liked_recipes', "cf_liked_recipes_health_score", "diet", 'time', 'ingredients', 'r1', 'r1_healthscore', 'r1_utility', 'r1_cf_score', 'pref reco better than habits', 'r2', 'r2_healthscore', 'r2_utility', 'r2_cf_score', 'healthier reco better than habits', 'utility healthier as good as utility pref']

class TestCora():
    def __init__(self, timeit, autotest_script=None, liked_recipes=None, csv_output=False):
        print(autotest_script)
        print(liked_recipes)

        '''
        :param timeit: Bool, do you want to know how much time it takes for Cora to generate a response?
        :param autotest_script: (optional), if you want to test Cora with a pre-writen scenario / script
        :param liked_recipes: if using CF (or hybrid rinvolving CF), do you want to specify a user profile of liked recipes for the user? (if not, set up randomly)
        '''
        self.name = "TestCora"
        self.autotest_script = autotest_script
        self.autotest_script_index = 0
        self.timeit = timeit

        self.liked_recipes = liked_recipes

        self.client_id = "test" + datetime.datetime.now().__str__()
        self.create_services()
        self.use_local_DB_bool = False

        self.csv_output = csv_output
        if csv_output:
            self.csv_rows = list()
            # print(self.liked_recipes)
            self.liked_recipes_hs = get_avg_healthScore(self.liked_recipes)
            self.csv_current_row = [self.liked_recipes, self.liked_recipes_hs]
            self.parse_diet, self.parse_time, self.parse_ingredients = False, False, False
            self.pref_recipe_hs, self.healthier_recipe_hs = None, None
            self.pref_recipe_utility, self.healthier_recipe_utility = None, None


    def set_use_local_DB_value(self, val):
        self.use_local_DB_bool = val
        for service in self.services:
            if "DM" in service.name:
                service.set_use_local_recipe_DB(val)

    def start_testCora(self):
        bool_continue = True
        if not self.autotest_script:
            print(colored("####################################################################################################", "yellow"))
            print(colored("You are about to test the full Cora-system (server side).\n","yellow"))
            print(colored("Because you're testing the server side, this test is LOCAL and nothing transits through firebase.", "yellow"))
            print(colored("Note that the data corresponding to this test is still be saved locally by the DataCollector module.\n", "yellow"))
            if self.use_local_DB_bool:
                utterance = input(colored("/!\\/!\\/!\\ We'll be using the local recipe DB --> queries to the local DB are NOT personalized with the user's preferences.\nAre you OK with that? (y: yes, q: no, cancel and quit): ", "yellow"))
                if utterance == "q":
                    self.quit()
                    bool_continue = False
                else:
                    print(colored("Nice!","yellow"))
            if bool_continue:
                print(colored("Enjoy your interaction with Cora!", "yellow"))
                print(colored("####################################################################################################","yellow"))
        if not self.autotest_script or bool_continue:
            self.subscribe_whiteboard(config.MSG_NLG + self.client_id)
            self.subscribe_whiteboard(config.MSG_DATACOL_OUT + self.client_id)
            self.timer_response_time = None
            self.next_input()

    def create_services(self):
        self.services = list()
        for module_config in config_modules.modules.modules:
            args = list(module_config.values())[2:]
            args.append(self.timeit)
            # print(*args)
            new_module = module_config["module"](self.client_id, *args)
            self.services.append(new_module)

        # star services in dedicated threads
        for s in self.services:
            s.start_service()
            if "KBRS" in s.name and self.liked_recipes:
                s.set_user_ratings_for_cf([[rid, 5] for rid in self.liked_recipes])

    def parse_user_pref(self, sentence):
        if self.parse_diet:
            self.csv_current_row.append(sentence)
            self.parse_diet = False
        elif self.parse_time:
            self.csv_current_row.append(sentence)
            self.parse_time = False
        elif self.parse_ingredients:
            self.csv_current_row.append(sentence)
            self.parse_ingredients = False



    def parse_reco_info(self, message, sentence):
        if 'rids' in message.keys() and message['rids']:
            for i, rid in enumerate(message['rids']):
                self.csv_current_row.append(rid)
                hs = get_healthScore(rid)
                self.csv_current_row.append(hs)
                utility = message['utilities'][i]
                self.csv_current_row.append(utility)
                self.csv_current_row.append(message['cf_scores'][i])
                if i == 0:
                    self.pref_recipe_hs = hs
                    self.pref_recipe_utility = utility
                    # is pref reco healthier than habits?
                    print(self.pref_recipe_hs, self.liked_recipes_hs)
                    if self.pref_recipe_hs < self.liked_recipes_hs:
                        self.csv_current_row.append(True)
                    else:
                        self.csv_current_row.append(False)
                elif i == 1:
                    self.healthier_recipe_hs = hs
                    self.healthier_recipe_utility = utility
                    # is healthier reco healthier than habits?
                    if self.healthier_recipe_hs < self.liked_recipes_hs:
                        self.csv_current_row.append(True)
                    else:
                        self.csv_current_row.append(False)
                    # is healthier recipe utility as good as pref recipe utility ?
                    if self.healthier_recipe_utility >= self.pref_recipe_utility:
                        self.csv_current_row.append(True)
                    else:
                        self.csv_current_row.append(False)

        if "Any specific diet or intolerances I should be aware of?" in sentence:
            self.parse_diet = True
        elif "How much time do you want to spend cooking tonight?" in sentence:
            self.parse_time = True
        elif "Is there any food you'd like to use? Something already in your kitchen or that you could buy?" in sentence:
            self.parse_ingredients = True

    # def parse_NLG_for_csv(self, message, sentence):
        # self.parse_user_pref(sentence)
        # self.parse_reco_info(message)


    def publish_whiteboard(self, message, topic):
        whiteboard.publish(message, topic)

    def save_to_csv(self):
        with open(csv_path, 'a') as fcsv:
            csv_writer = csv.writer(fcsv)
            for row in self.csv_rows:
                csv_writer.writerow(row)

    def on_whiteboard_message(self, message, topic):
        if config.MSG_NLG in topic:
            print("Response time: %.3f sec" % (time.time() - self.timer_response_time))
            # if message['send_several_messages']:
            for sentence_delay_dict in message["sentences_and_delays"]:
                sentence, delay = sentence_delay_dict['sentence'], sentence_delay_dict['delay']
                # print(sentence, delay)
                if delay:
                    print("delay: %.2f" % delay)
                    time.sleep(delay)
                print(colored("Cora says: "+sentence, "red"))
                self.publish_whiteboard({"dialog": sentence}, config.MSG_DATACOL_IN + self.client_id)

                if self.csv_output:
                    self.parse_reco_info(message, sentence=sentence)

            if message["intent"] == "bye":
                if self.csv_output:
                    self.csv_rows.append(self.csv_current_row)
                    self.save_to_csv()
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
            if self.csv_output:
                self.parse_user_pref(sentence=utterance)
            print(colored("User: "+utterance, "yellow"))
        else:
            utterance = input(colored("Enter text (q to quit): ", "yellow"))
            if utterance == 'q':
                self.quit()
        topic = config.MSG_SERVER_IN + self.client_id
        self.timer_response_time = time.time()
        whiteboard.publish(utterance, topic)

    def quit(self):
        for c in self.services:
            c.stop_service()
        # exit(0)


def get_test_scripts():
    users_scripts = dict()
    users_liked_recipes = dict()

    small_talk = ["hi", "user", "Fine", "vegetarian", "healthy"]

    file_path = 'food/resources/data_collection/CHI/res.csv'
    with open(file_path, 'r') as fin:
        df = pd.read_csv(fin)

    for index, row in df.iterrows():
        answers = list()
        answers = small_talk + [row['diet'], row['time'], row['ingredients'], "no"]
        users_scripts[row['prolific ID']] = answers
        users_liked_recipes[row['prolific ID']] = row['liked recipes'][2:-2].split("', '")

    return users_scripts, users_liked_recipes



if __name__ == "__main__":

    liked_recipes = None

    argp = argparse.ArgumentParser()
    argp.add_argument('domain', metavar='domain', type=str, help='Domain to test (e.g. movies? food?)')
    argp.add_argument("--autotest", help="To test the system with a predefined script (to write bellow directly in the python file)", action="store_true")
    argp.add_argument("--randomtest", help="To test the system with random utterances (chosen from list written in this file)", action="store_true")
    argp.add_argument("--test", help="To test the NLU module yourself", action="store_true")
    argp.add_argument("--logs", help="If you want to see the python logs in the console", action="store_true")
    argp.add_argument("--timeit", help="If you want get the execution time for each module", action="store_true")

    hi = ["hi", "hello", "good morning", "hiya", "hallo"]
    i_am_emotion = ["i m tired", "good", "amazing", "i feel great", "OK", "fine", "i m good", "exhausted", "i had a good night and i feel great this morning!", "not good", "i feel bad", "i am in a bad mood", "i am sick", "I have a headache"]
    diet = ["Dairy free", "Gluten Free", "Low carbs", "Ketonic", "Vegetarian", "Vegan", "Pescetarian"]
    time_options = ["I have time", "I don t have time", "I am in a rush", "something quick", "I have plenty of time", "not in a rush"]
    accept_recipe = ["no", "something else", "not that", "seems good", "yes", "sure", "I don t like salmon", "i don t like salad", "i don t like chicken"]
    conversation_stages = [hi, i_am_emotion, diet, time_options, accept_recipe]


    autotest_scripts = dict()
    # autotest_scripts["errcor_pop_from_empty_list"] = ["hello", "Lucile", "better now", "soup", "it s healthy and light", "bot too much yet", "very", 'i m vegetarian', "20 min", "nop",
    #                                                  "why not", "sure", 'something else than soup?', 'yep', "yep" 'no', 'ok', "seems nice", "ya", "good", "yes", "yes", "yes", "yes", "yes", "yes", "yes", "no thanks"]
    # autotest_scripts['test1'] = ['hi', 'Lucile', "yup", 'what my husband cooks', 'because i take care of the baby so i don\'t cook', 'vegan', 'up to an hour', 'broccoli', 'I prefer Spicy Garlic Lime Chicken']
    small_talk = ["hi", "user", "Fine", "vegetarian", "healthy"]
    # autotest_scripts['user1'] = small_talk + ['hi', 'user', 'Fine', 'vegetarian', 'healthy', 'vegan die', '40 min', 'lettuce, cauliflower, rice', 'no']
    # autotest_scripts['user2'] = small_talk + ["None", "1h", "sweet potato", "No"]
    autotest_scripts['user3'] = small_talk + ["None", "2000min", "pasta", "No"]
    # liked_recipes = dict()
    # liked_recipes['user1'] = ['9615/healthy-banana-cookies/', '15836/strawberry-pie-ii/', '11314/delicious-raspberry-oatmeal-cookie-bars/', '17981/one-bowl-chocolate-cake-iii/', '25787/coconut-macaroons-iii/', '15475/stephens-chocolate-chip-cookies/']
    # liked_recipes['user2'] = ['9615/healthy-banana-cookies/', '15836/strawberry-pie-ii/', '11314/delicious-raspberry-oatmeal-cookie-bars/', '17981/one-bowl-chocolate-cake-iii/', '25787/coconut-macaroons-iii/', '15475/stephens-chocolate-chip-cookies/']
    # liked_recipes['user3'] = ['9615/healthy-banana-cookies/', '15836/strawberry-pie-ii/', '11314/delicious-raspberry-oatmeal-cookie-bars/', '17981/one-bowl-chocolate-cake-iii/', '25787/coconut-macaroons-iii/', '15475/stephens-chocolate-chip-cookies/']

    # autotest_scripts, liked_recipes = get_test_scripts()
    #
    # liked_recipes = dict()
    # liked_recipes['user2'] = ['9615/healthy-banana-cookies/', '15836/strawberry-pie-ii/', '11314/delicious-raspberry-oatmeal-cookie-bars/', '17981/one-bowl-chocolate-cake-iii/', '25787/coconut-macaroons-iii/', '15475/stephens-chocolate-chip-cookies/']


    CSV_OUTPUT = True

    args = argp.parse_args()
    timeit = args.timeit if args.timeit else False
    if not args.logs:
        log.setLevel(logging.CRITICAL)

    try:
        test = None
        if(args.domain in ["movies", "food"]):
            config_modules.modules.set_domain(args.domain)
            if args.autotest and autotest_scripts:
                if CSV_OUTPUT:
                    with open(csv_path, 'w') as fcsv:
                        csv_writer = csv.writer(fcsv)
                        csv_writer.writerow(csv_first_row)
                for script_name, script in autotest_scripts.items():
                    n_iter = 1
                    if CSV_OUTPUT:
                        n_iter = 2
                    for i in range(n_iter):
                        print(colored(script_name, "blue"))
                        if liked_recipes:
                            test = TestCora(timeit, script, liked_recipes[script_name], CSV_OUTPUT)
                        else:
                            test = TestCora(timeit, script, None, CSV_OUTPUT)
                        test.start_testCora()

            elif args.test:
                test = TestCora(timeit)
                test.start_testCora()

            elif args.randomtest:
                script = list()
                for elt in conversation_stages:
                    script.append(random.choice(elt))
                for i in range(10):
                    script.append(random.choice(conversation_stages[-1]))
                test = TestCora(timeit, script)
                test.start_testCora()

            else:
                argp.print_help()
        else:
            argp.print_help()

    except:
        print("except")
        if test:
            test.quit()
        exceptiondata = traceback.format_exc().splitlines()
        print(exceptiondata[0])
        print("  [...]")
        for line in exceptiondata[-9:]:
            # for line in exceptiondata:
            print(line)


