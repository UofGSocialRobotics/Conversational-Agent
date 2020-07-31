import re
import json
import random
import statistics as stats
from termcolor import colored

import whiteboard_client as wbc
import helper_functions as helper
# from food.collaborative_filtering import CFRS
from food.CF_implicit_ratings import ImplicitCFRS, auc_score
import food.RS_utils as rs_utils
import config
import food.food_config as fc
from ca_logging import log
import food.resources.recipes_DB.allrecipes.nodejs_scrapper.consts as consts
from food.healthy_RS import HealthyRS

N_RECIPES_TO_DISPLAY_PREFGATHERING = 30
N_RECIPES_TO_DISPLAY_EVAL = 30
N_RECIPES_TO_RECOMMEND = 5
N_RECIPES_PROFILE = 5

RANDOM_SAMPLE_FROM_N_LEAST_RECOMMENDED = (N_RECIPES_TO_DISPLAY_EVAL - N_RECIPES_TO_RECOMMEND) * 3


class RS(wbc.WhiteBoardClient):
    def __init__(self, clientid, subscribes, publishes, resp_time=False):
        self.user_name = clientid
        subscribes = helper.append_c_to_elts(subscribes, clientid)
        publishes = [p + clientid for p in publishes]
        wbc.WhiteBoardClient.__init__(self, name="RS"+clientid, subscribes=subscribes, publishes=publishes, resp_time=resp_time)

        # self.ratings_pref_gathering_list = list()
        # self.ratings_reco_list = list()
        self.pref_gathering_liked_recipes = list()
        self.reco = None
        self.recommended_recipes_liked_by_user = list()
        self.eval_reco_liked_recipes = None

        self.implicit_rs = ImplicitCFRS()
        if config.rs_eval_cond == config.cond_health:
            self.healthy_rs = HealthyRS.getInstance()
        # else:
        if config.rs_eval_cond == config.cond_hybrid:
            self.healthy_bias = True
            self.implicit_rs.set_healthy_bias(healthy_bias=True)
        else:
            self.healthy_bias = False
            self.implicit_rs.set_healthy_bias(healthy_bias=False)
        self.implicit_rs.start()

        with open(consts.json_xUsers_Xrecipes_path, 'r') as f:
            content = json.load(f)
        self.recipes_dict = content['recipes_data']

        self.total_recipes = len(list(self.recipes_dict.keys()))

        self.leanr_pref_recipes_sent = list()
        self.eval_reco_recipes_sent = list()
        self.reco_list = None
        self.eval_data = dict()
        self.rid_to_pref_score = dict()
        self.rid_to_final_score = dict()


    def parse_client_msg(self, msg):
        rid = msg.split("(")[1].split(")")[0]
        r = int(re.search(r'\d+', msg).group())
        return rid, r

    def get_info_to_send_recipe(self, rid):
        rdata = dict()
        rdata['title'] = self.recipes_dict[rid]['title']
        if 'description' in self.recipes_dict[rid].keys():
            rdata['description'] = self.recipes_dict[rid]['description']
        else:
            rdata['description'] = "--"
        rdata['image_url'] = self.recipes_dict[rid]['image_url']
        rdata['rating'] = self.recipes_dict[rid]['rating']
        rdata['n_ratings'] = self.recipes_dict[rid]['n_reviews_collected']
        rdata['id'] = rid
        if 'Prep' in self.recipes_dict[rid]['time_info'].keys():
            rdata['time_prep'] = self.recipes_dict[rid]['time_info']['Prep']
        else:
            rdata['time_prep'] = "--"
        if 'Cook' in self.recipes_dict[rid]['time_info'].keys():
            rdata['time_cook'] = self.recipes_dict[rid]['time_info']['Cook']
        else:
            rdata['time_cook'] = "--"
        if 'Total' in self.recipes_dict[rid]['time_info'].keys():
            rdata['time_total'] = self.recipes_dict[rid]['time_info']['Total']
        else:
            rdata['time_total'] = "--"
        if 'Servings' in self.recipes_dict[rid]['time_info'].keys():
            rdata['servings'] = self.recipes_dict[rid]['time_info']['Servings']
        else:
            rdata['servings'] = "--"
        FSA = self.recipes_dict[rid]['FSAscore']
        if FSA < 7:
            rdata['FSAcolour'] = "green"
        elif FSA > 9:
            rdata['FSAcolour'] = "red"
        else:
            rdata['FSAcolour'] = "orange"
        # log.debug("%s %d %s" % (rid, FSA, rdata["FSAcolour"]))


        ingredients_list = self.recipes_dict[rid]['ingredients']
        n_ingredients = len(ingredients_list)
        # print(type(n_ingredients))
        n_ingredients_by_col, remainder = n_ingredients // 3, n_ingredients % 3
        # print(n_ingredients_by_col, remainder)
        extra_in_col_1 = 0 if remainder == 0 else 1
        extra_in_col_2 = 1 if remainder == 2 else 0
        limit_col1 = n_ingredients_by_col+extra_in_col_1
        limit_col2 = n_ingredients_by_col*2+extra_in_col_1+extra_in_col_2
        col1 = ingredients_list[:limit_col1]
        col2 = ingredients_list[limit_col1:limit_col2]
        col3 = ingredients_list[limit_col2:]
        # print(n_ingredients, n_ingredients_by_col, remainder, extra_in_col_1, extra_in_col_2)
        # print(limit_col1, limit_col2)
        rdata['ingredients'] = dict()
        rdata['ingredients']["col1"], rdata['ingredients']["col2"], rdata['ingredients']["col3"] = col1, col2, col3

        rdata['instructions'] = self.recipes_dict[rid]['instructions']

        return rdata

    def get_reco(self, ratings_list):
        # get hybrid / pref reco
        reco = self.implicit_rs.get_reco(self.user_name, ratings_list, n_reco=self.total_recipes-N_RECIPES_PROFILE, verbose=False)
        # print(reco)
        self.save_final_score(reco)
        if self.healthy_bias:
            self.save_pref_score(reco)
        if config.rs_eval_cond == config.cond_health:
            reco = self.healthy_rs.get_reco(self.user_name, ratings_list, n_reco=N_RECIPES_TO_RECOMMEND + 10, verbose=False)
        reco_20 = [item[1] for item in reco]
        self.reco = list()
        for rid in reco_20:
            if rid not in self.leanr_pref_recipes_sent:
                self.reco.append(rid)
            else:
                log.debug("%s already presented to user in learn-pref phase; eliminating it from reco list." % rid)
            if len(self.reco) == N_RECIPES_TO_RECOMMEND:
                break


    def save_pref_score(self, reco_list):
        for x in reco_list:
            self.rid_to_pref_score[x[1]] = x[3]

    def save_final_score(self, reco_list):
        for x in reco_list:
            self.rid_to_final_score[x[1]] = x[2]

    def get_pref_score(self, rid_list):
        pref_scores = list()
        for rid in rid_list:
            pref_scores.append(self.rid_to_pref_score[rid])
        return stats.mean(pref_scores)

    def get_final_score(self, rid_list):
        pref_scores = list()
        for rid in rid_list:
            pref_scores.append(float(self.rid_to_final_score[rid]))
        log.debug(pref_scores)
        return stats.mean(pref_scores)

    def treat_message(self, msg, topic):
        # print(msg, topic)
        super(RS, self).treat_message(msg, topic)

        # Send recipes to learn user's pref
        if msg == config.MSG_RS_LEARNING_PHASE:
            recipes_ids = self.recipes_dict.keys()
            random_recipes = random.sample(recipes_ids, N_RECIPES_TO_DISPLAY_PREFGATHERING)
            recipes_to_send = list()
            for rid in random_recipes:
                rdata = self.get_info_to_send_recipe(rid)
                recipes_to_send.append(rdata)
                self.leanr_pref_recipes_sent.append(rid)
            msg = {"intent": "learn_pref", "recipes": recipes_to_send}
            self.publish(msg, topic=self.publishes[0])

        # Send a mix or recommended and random recipes to evaluate system
        elif msg == config.MSG_RS_EVAL_PHASE:
            # log.debug(self.leanr_pref_recipes_sent)
            # log.debug(self.reco)
            recipes_ids = self.recipes_dict.keys()
            to_chose_from = helper.diff_list(list(recipes_ids), self.leanr_pref_recipes_sent + self.reco)

            random_recipes = random.sample(to_chose_from, N_RECIPES_TO_DISPLAY_EVAL - N_RECIPES_TO_RECOMMEND)
            # log.debug(len(self.bad_reco))
            # log.debug("to choose_from")
            # log.debug(to_chose_from)

            self.eval_data['final_score_reco'] = self.get_final_score(self.reco)
            # self.eval_data['final_score_others'] = self.get_final_score(random_recipes)
            if self.healthy_bias:
                self.eval_data['pref_score_reco'] = self.get_pref_score(self.reco)
                # self.eval_data['pref_score_others'] = self.get_pref_score(random_recipes)
            else:
                self.eval_data['pref_score_reco'] = None
                # self.eval_data['pref_score_others'] = None
            recipes_to_send_ids_list = random_recipes + self.reco
            log.debug(recipes_to_send_ids_list)
            random.shuffle(recipes_to_send_ids_list)
            recipes_to_send = list()
            for rid in recipes_to_send_ids_list:
                rdata = self.get_info_to_send_recipe(rid)
                recipes_to_send.append(rdata)
                self.eval_reco_recipes_sent.append(rid)
            msg = {"intent": "eval_reco", "recipes": recipes_to_send}
            self.publish(msg, topic=self.publishes[0])

        # Save user's preferences and generate recommendation
        elif isinstance(msg, list) and not self.reco:
            # print(colored(msg, 'blue'))
            for rid in msg:
                if rid in self.recipes_dict.keys():
                    self.pref_gathering_liked_recipes.append(rid)
                else:
                    log.error("rid %s unknown!" % rid)
            ratings_list = [[rid, 5] for rid in self.pref_gathering_liked_recipes]
            self.get_reco(ratings_list)
            # self.get_bad_reco(ratings_list)

            
        # Save user's evaluation of reco 
        elif isinstance(msg, list) and self.reco:
            self.eval_reco_liked_recipes = msg
            for rid in msg:
                if rid in self.reco:
                    self.recommended_recipes_liked_by_user.append(rid)

            self.eval_data["reco"] = self.reco
            tp = len(self.recommended_recipes_liked_by_user)
            self.eval_data["P_predict"] = N_RECIPES_TO_RECOMMEND
            self.eval_data["N_predict"] = N_RECIPES_TO_DISPLAY_EVAL - N_RECIPES_TO_RECOMMEND
            self.eval_data["P"] = len(msg)
            self.eval_data["N"] = N_RECIPES_TO_DISPLAY_EVAL - len(msg)
            self.eval_data["TP"] = tp
            self.eval_data["FP"] = N_RECIPES_TO_RECOMMEND - tp
            fn = len(msg) - tp
            self.eval_data["FN"] = fn
            self.eval_data["TN"] = (N_RECIPES_TO_DISPLAY_EVAL - N_RECIPES_TO_RECOMMEND) - fn
            self.eval_data["total_recommended_recipes"] = N_RECIPES_TO_RECOMMEND
            self.eval_data["precision"] = self.eval_data["TP"] / float(self.eval_data["TP"] + self.eval_data["FP"])
            self.eval_data["recall"] = self.eval_data["TP"] / float(self.eval_data["TP"] + self.eval_data["FN"])
            self.eval_data["cond"] = config.rs_eval_cond
            if self.eval_data["precision"] == 0 or self.eval_data["recall"] == 0:
                self.eval_data["f1"] = 0
            else:
                self.eval_data["f1"] = 2 * self.eval_data["precision"] * self.eval_data["recall"] / (self.eval_data["precision"] + self.eval_data["recall"])
            self.eval_data["accuracy"] = float(self.eval_data["TP"] + self.eval_data["TN"]) / N_RECIPES_TO_DISPLAY_EVAL
            # AUC -- pred and acutal are vectors of vales btn 0 and 1
            pred, actual = list(), list()
            for rid in self.eval_reco_recipes_sent:
                if rid in self.reco:
                    pred.append(1)
                else:
                    pred.append(0)
                if rid in msg:
                    actual.append(1)
                else:
                    actual.append(0)
            auc = auc_score(pred, actual)
            self.eval_data["AUC"] = auc
            print(self.eval_data)
            self.publish({"rs_eval_data": self.eval_data}, topic=self.publishes[1])



        else:
            log.error("Not implemented yet: don't know what to do on reception of %s" % msg)

