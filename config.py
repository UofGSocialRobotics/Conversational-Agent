import movies
from movies import NLU as movies_NLU
from movies import DM as movies_DM
from movies import NLG as movies_NLG
from movies import dum_sentiment_analysis as movies_SA
import food
from food import DM as food_DM
from food import NLG as food_NLG
from food import NLU as food_NLU
import ca_logging as logging
import amt_info
####################################################################################################
##                                Using broker or websockets on localhost                         ##
####################################################################################################

BROKER = "broker"
WEBSOCKETS = "websockets"
# USING = BROKER
USING = WEBSOCKETS

####################################################################################################
##                                        Broker config                                           ##
####################################################################################################
ADDRESS = "mqtt.eclipse.org" #iot.eclipse.org
PORT = 1883

# Connection timeout, in secondes
CONNECTION_TIMEOUT = 60 * 1


####################################################################################################
##                                           Messages                                             ##
####################################################################################################
## Main topic
MSG_MAIN_TOPIC = "UoGSR/ca/"

## Client publishes on
MSG_CLIENT = MSG_MAIN_TOPIC+"Client/"

## For NLU, Server publishes on
MSG_SERVER_IN= MSG_MAIN_TOPIC+"Server_in/"

## For DM, NLU publishes on
MSG_NLU = MSG_MAIN_TOPIC+"NLU/"

## FOR DM, SentimentAnalysis publishes on
MSG_SA = MSG_MAIN_TOPIC+"SA/"

## For NLG, DM published on
MSG_DM = MSG_MAIN_TOPIC+"DM/"

## For main server, NLG publishes on
MSG_NLG = MSG_MAIN_TOPIC+"NLG/"

## For client, main server publishes on
MSG_SERVER_OUT = MSG_MAIN_TOPIC+"Server_out/"

## For AMT info module, server publishes on
MSG_AMTINFO_IN = MSG_MAIN_TOPIC+"AMTinfo_in/"

## For server, AMT info module publishes on
MSG_AMTINFO_OUT = MSG_MAIN_TOPIC+"AMTinfo_out/"

# Connection message from client:
MSG_CONNECTION = "new client connected"

# Confirm connection to client:
MSG_CONFIRM_CONNECTION = "Connection confirmed"

# AMT id message
MSG_AMTINFO = "amt_id"

# ACK AMT id
MSG_AMTINFO_ACK = "ACK AMT_INFO"


## NLU
NLU_subscribes = [MSG_SERVER_IN]
NLU_publishes = MSG_NLU

## DM
DM_subscribes = [MSG_NLU, MSG_SA]
DM_publishes = MSG_DM

## NLG
NLG_subscribes = [MSG_DM]
NLG_publishes = MSG_NLG

## Sentiment analysis
SentimentAnalysis_subscribes = [MSG_SERVER_IN]
SentimentAnalysis_publishes = MSG_SA

## AMT_info
AMTinfo_subscribes = [MSG_AMTINFO_IN]
AMTinfo_publishes = MSG_AMTINFO_OUT

####################################################################################################
##                                          Modules                                               ##
####################################################################################################
# NLU = None
# DM = None
# NLG = None
# SentimentAnalysis = None

class Modules:
    """Singleton class"""
    __instance = None

    @staticmethod
    def getInstance():
        """
        :return: the unique whiteboard object
        """
        if Modules.__instance == None:
            Modules()
        return  Modules.__instance


    def __init__(self):
        """
        This constructor in virtually private.
        :param domain:
        """
        if Modules.__instance != None:
            logging.log.error("Singleton Class: contructor should not be called. Use Modules.getInstance()")
        else:
            Modules.__instance = self
            self.NLU = None
            self.DM = None
            self.SentimentAnalysis = None
            self.NLG = None
            self.AMTinfo = amt_info.AMT_info

    def set_domain(self, domain):
        if domain == "movies":
            self.NLU = movies_NLU.RuleBasedNLU
            self.DM = movies_DM.DM
            self.NLG = movies_NLG.NLG
            self.SentimentAnalysis = movies_SA.SentimentAnalysis
            logging.log.info("(config.py) Set domain as movies.")
        elif domain == "food":
            self.NLU = food_NLU.NLU
            self.DM = food_DM.DM
            self.NLG = food_NLG.NLG
            self.SentimentAnalysis = movies_SA.SentimentAnalysis
            logging.log.info("(config.py) Set domain as food.")
        else:
            logging.log.error("No %s domain" % domain)
            exit(0)

modules = Modules.getInstance()



