import re
import json
import random

import whiteboard_client as wbc
import helper_functions as helper
from food.collaborative_filtering import CFRS
import food.RS_utils as rs_utils
import config
import food.food_config as fc
from ca_logging import log

class RS(wbc.WhiteBoardClient):
    def __init__(self, clientid, subscribes, publishes, resp_time=False):
        self.user_name = clientid
        subscribes = helper.append_c_to_elts(subscribes, clientid)
        publishes = publishes + clientid
        wbc.WhiteBoardClient.__init__(self, name="RS"+clientid, subscribes=subscribes, publishes=publishes, resp_time=resp_time)

        self.ratings_list = list()

        self.rs = CFRS.getInstance()

        with open(rs_utils.file_path, 'r') as f:
            content = json.load(f)
        self.recipes_dict = content['recipes_data']

        self.already_sent = list()


    def send_random_recipe(self):
        left_to_chose_from = [rid for rid in list(self.recipes_dict.keys()) if not rid in self.already_sent]
        rid = random.choice(left_to_chose_from)
        r = self.recipes_dict[rid]
        # r = self.recipes_dict['/recipes/parmesan-spring-chicken']

        r['comments'] = None
        del r['comments']
        ingredients_list = r['ingredients']
        # print(type(n_ingredients))
        n_ingredients = len(ingredients_list)
        n_ingredients_by_col, remainder = n_ingredients // 3, n_ingredients % 3
        log.debug(rid)
        log.debug(n_ingredients)
        log.debug("%d, %d" % (n_ingredients_by_col, remainder))
        extra_in_col_1 = 0 if remainder == 0 else 1
        extra_in_col_2 = 1 if remainder == 2 else 0
        limit_col1 = n_ingredients_by_col+extra_in_col_1
        limit_col2 = n_ingredients_by_col*2+extra_in_col_1+extra_in_col_2
        log.debug("%d, %d" % (limit_col1, limit_col2))
        log.debug(ingredients_list)
        if limit_col1 == 1:
            col1 = [ingredients_list[0]]
        else:
            col1 = ingredients_list[:limit_col1]
        if (limit_col2 - limit_col1) == 1:
            col2 = [ingredients_list[limit_col1]]
        elif (limit_col2 - limit_col1) == 0:
            col2 = []
        else:
            col2 = ingredients_list[limit_col1:limit_col2]
        if n_ingredients - limit_col2 == 1:
            col3 = [ingredients_list[limit_col2]]
        elif n_ingredients - limit_col2 == 0:
            col3 = []
        else:
            col3 = ingredients_list[limit_col2:]
        # print(n_ingredients, n_ingredients_by_col, remainder, extra_in_col_1, extra_in_col_2)
        # print(limit_col1, limit_col2)
        r['ingredients'] = dict()
        r['ingredients']["col1"], r['ingredients']["col2"], r['ingredients']["col3"] = col1, col2, col3
        msg = {"intent": "get_rating", "recipe": r}
        self.already_sent.append(rid)
        self.publish(msg)


    def get_reco(self):
        if len(self.ratings_list) < 10:
            raise ValueError("Not enough ratings to give reco!")
        return self.rs.get_reco(self.user_name, self.ratings_list)


    def parse_client_msg(self, msg):
        rid = msg.split("(")[1].split(")")[0]
        r = int(re.search(r'\d+', msg).group())
        return rid, r


    def treat_message(self, msg, topic):
        # print(msg, topic)
        super(RS, self).treat_message(msg,topic)

        if msg == config.MSG_GET_RECO:
            reco = self.get_reco(self.user_name, self.ratings_list)
            data = {fc.reco: reco}
            self.publish(data)

        else:
            rid, r = self.parse_client_msg(msg)
            self.ratings_list.append([rid, r])
            log.debug(self.ratings_list)
            self.send_random_recipe()
