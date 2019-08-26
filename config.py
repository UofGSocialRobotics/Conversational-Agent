import cryptography.fernet as fernet
import json
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
import data_collection


####################################################################################################
##                                        Firebase config                                         ##
####################################################################################################
FIREBASE_CONFIG = {
    "apiKey": b'gAAAAABdY8Pt-1IvwSbibNonOERI8SMupgGPhcIyQF3iz74yY3TYkzkJSi42orHfpbmqEcL84srSEqafnyYnbm0tl2e4gU9j6dtbq2KbQ2aYmIYx9kFCUU2oAgDMfPlt9aMrqTWNn3zU',
    "authDomain": b'gAAAAABdY8SCa7RBGJwU9a4ZbNEBDbBwu7I8IH-S22enmEKY5X_dTrcqBJLEyVj5s9yI6v2v7QGJQGO4fJc83u7lnJSerVY1Q0BoKfmOXjrlvZkyBQpphXs=',
    "databaseURL": b'gAAAAABdY8S6Hlr38Nx4SLHDTJMb4vyY6DXfVV-hnLPguLR549fPPq_VGjheCXXUHXHh1MD57tQmkyWzWY4a2QPe3xRxjoD2qnIX5YcGx_6kZ4ApClwri0BDVBfpFSZpSXtBemIxQYIu',
    "storageBucket": b'gAAAAABdY8TtKf93x7ZC7gj1nC2dRx1JghGY74-vHqZq0nXc9FH51fJjXDzOvUZKcQRSMteMjIIKshHBz8sx4n_BTlgdTP64LN4tG9-hWwaGBJ5KgLfOlZA=',
}

with open("resources/encryption_key.json", 'rb') as f:
    key = json.load(f)["encryption_key"]
print(key)
f = fernet.Fernet(key.encode())
for key, value in FIREBASE_CONFIG.items():
    FIREBASE_CONFIG[key] = f.decrypt(value).decode()

# Connection timeout, in secondes
CONNECTION_TIMEOUT = 60 * 10

####################################################################################################
##                                           Messages                                             ##
####################################################################################################

## Client publishes on
MSG_CLIENT = "Client/"

## For NLU, Server publishes on
MSG_SERVER_IN= "Server_in/"

## For DM, NLU publishes on
MSG_NLU = "NLU/"

## FOR DM, SentimentAnalysis publishes on
MSG_SA = "SA/"

## For NLG, DM published on
MSG_DM = "DM/"

## For main server, NLG publishes on
MSG_NLG = "NLG/"

## For client, main server publishes on
MSG_SERVER_OUT_DIALOG = "dialog"
MSG_SERVER_OUT_ACK = "ACK"

## For AMT info module, server publishes on
MSG_DATACOL_IN = "DataCollector_in/"

## For server, AMT info module publishes on
MSG_DATACOL_OUT = "DataCollector_out/"

# Client to server, message content:
MSG_CONNECTION = "client connected"

# ACK AMT id
MSG_ACK_AMT_INFO = "ack amt info"
MSG_ACK_CONNECTION = "ack new connection"


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

## DataCollector
DataCollector_subscribes = [MSG_DATACOL_IN]
DataCollector_publishes = MSG_DATACOL_OUT

####################################################################################################
##                                        Firebase Keys                                           ##
####################################################################################################

# High level keys
FIREBASE_KEY_USERS = "Users"
FIREBASE_KEY_SESSIONS = "Sessions"

# Low level keys
FIREBASE_KEY_DATETIME = "datetime"
FIREBASE_KEY_CLIENTID = "client_id"
FIREBASE_KEY_ACKFOR = "for"


# Session keys
# Keys used to write
FIREBASE_KEY_TEXT = "text"
FIREBASE_KEY_SOURCE = "source"
FIREBASE_VALUE_SOURCE_CLIENT = "client"
FIREBASE_VALUE_SOURCE_AGENT = "agent"
FIREBASE_KEY_ACK = "ack"
# Keys used to read
FIREBASE_KEY_AMTID = "amt_id"
FIREBASE_KEY_DATACOLLECTION = "data_collection"
# Keys used to write and read
FIREBASE_KEY_DIALOG = "dialog"


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
            self.DataCollector = data_collection.DataCollector

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



