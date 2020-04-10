import re

import whiteboard_client as wbc
import helper_functions as helper
from food.collaborative_filtering import CFRS
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
            print(self.ratings_list)
