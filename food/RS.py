import re
import json
import random

import whiteboard_client as wbc
import helper_functions as helper
# from food.collaborative_filtering import CFRS
from food.CF_implicit_ratings import ImplicitCFRS, auc_score
import food.RS_utils as rs_utils
import config
import food.food_config as fc
from ca_logging import log
import food.resources.recipes_DB.allrecipes.nodejs_scrapper.consts as consts

N_RECIPES_TO_DISPLAY = 30
N_RECIPES_TO_RECOMMEND = 15


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

        self.rs = ImplicitCFRS()
        self.rs.set_healthy_bias(config.healthy_bias)
        self.rs.start()

        with open(consts.json_xUsers_Xrecipes_path, 'r') as f:
            content = json.load(f)
        self.recipes_dict = content['recipes_data']

        self.leanr_pref_recipes_sent = list()
        self.eval_reco_recipes_sent = list()
        self.reco_list = None


    def get_reco(self):
        if len(self.ratings_pref_gathering_list) < 10:
            raise ValueError("Not enough ratings to give reco!")
        return self.rs.get_reco(self.user_name, self.ratings_pref_gathering_list)


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
        return rdata

    def treat_message(self, msg, topic):
        # print(msg, topic)
        super(RS, self).treat_message(msg, topic)

        # Send recipes to learn user's pref
        if msg == config.MSG_RS_LEARNING_PHASE:
            recipes_ids = self.recipes_dict.keys()
            random_recipes = random.sample(recipes_ids, N_RECIPES_TO_DISPLAY)
            recipes_to_send = list()
            for rid in random_recipes:
                rdata = self.get_info_to_send_recipe(rid)
                recipes_to_send.append(rdata)
                self.leanr_pref_recipes_sent.append(rid)
            msg = {"intent": "learn_pref", "recipes": recipes_to_send}
            self.publish(msg, topic=self.publishes[0])

        # Send a mix or recommended and random recipes to evaluate system
        elif msg == config.MSG_RS_EVAL_PHASE:
            recipes_ids = self.recipes_dict.keys()
            to_chose_from = helper.diff_list(recipes_ids, self.leanr_pref_recipes_sent + self.reco)
            random_recipes = random.sample(to_chose_from, N_RECIPES_TO_DISPLAY - N_RECIPES_TO_RECOMMEND)
            recipes_to_send_ids_list = random_recipes + self.reco
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
            for rid in msg:
                if rid in self.recipes_dict.keys():
                    self.pref_gathering_liked_recipes.append(rid)
                else:
                    log.error("rid %s unknown!" % rid)
            ratings_list = [[rid, 5] for rid in self.pref_gathering_liked_recipes]
            self.reco = [item[1] for item in self.rs.get_reco(self.user_name, ratings_list, n_reco=N_RECIPES_TO_RECOMMEND, verbose=True)]
            
        # Save user's evaluation of reco 
        elif isinstance(msg, list) and self.reco:
            self.eval_reco_liked_recipes = msg
            for rid in msg:
                if rid in self.reco:
                    self.recommended_recipes_liked_by_user.append(rid)

            eval_data = dict()
            eval_data["reco"] = self.reco
            tp = len(self.recommended_recipes_liked_by_user)
            eval_data["P_predict"] = N_RECIPES_TO_RECOMMEND
            eval_data["N_predict"] = N_RECIPES_TO_DISPLAY - N_RECIPES_TO_RECOMMEND
            eval_data["P"] = len(msg)
            eval_data["N"] = N_RECIPES_TO_DISPLAY - len(msg)
            eval_data["TP"] = tp
            eval_data["FP"] = N_RECIPES_TO_RECOMMEND - tp
            fn = len(msg) - tp
            eval_data["FN"] = fn
            eval_data["TN"] = (N_RECIPES_TO_DISPLAY - N_RECIPES_TO_RECOMMEND) - fn
            eval_data["total_recommended_recipes"] = N_RECIPES_TO_RECOMMEND
            eval_data["precision"] = eval_data["TP"] / float(eval_data["TP"] + eval_data["FP"])
            eval_data["recall"] = eval_data["TP"] / float(eval_data["TP"] + eval_data["FN"])
            eval_data["cond"] = config.health_recsys_study_cond
            if eval_data["precision"] == 0 or eval_data["recall"] == 0:
                eval_data["f1"] = 0
            else:
                eval_data["f1"] = 2 * eval_data["precision"] * eval_data["recall"] / (eval_data["precision"] + eval_data["recall"])
            eval_data["accuracy"] = float(eval_data["TP"] + eval_data["TN"]) / N_RECIPES_TO_DISPLAY
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
            eval_data["AUC"] = auc
            print(eval_data)
            self.publish({"rs_eval_data": eval_data}, topic=self.publishes[1])



        else:
            log.error("Not implemented yet: don't know what to do on reception of %s" % msg)

