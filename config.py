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
from food import heath_diagnostic
import ca_logging as logging
import data_collection


####################################################################################################
##                                       Experimental conditions                                  ##
####################################################################################################
exp_type_food = "food"
exp_type_opinion = "opinion"
exp_type_feature = "feature"
EXPLANATION_TYPE = []


####################################################################################################
##                                        Firebase config                                         ##
####################################################################################################
FIREBASE_CONFIG = {
    "apiKey": b'gAAAAABdY8Pt-1IvwSbibNonOERI8SMupgGPhcIyQF3iz74yY3TYkzkJSi42orHfpbmqEcL84srSEqafnyYnbm0tl2e4gU9j6dtbq2KbQ2aYmIYx9kFCUU2oAgDMfPlt9aMrqTWNn3zU',
    "authDomain": b'gAAAAABdY8SCa7RBGJwU9a4ZbNEBDbBwu7I8IH-S22enmEKY5X_dTrcqBJLEyVj5s9yI6v2v7QGJQGO4fJc83u7lnJSerVY1Q0BoKfmOXjrlvZkyBQpphXs=',
    "databaseURL": b'gAAAAABdY8S6Hlr38Nx4SLHDTJMb4vyY6DXfVV-hnLPguLR549fPPq_VGjheCXXUHXHh1MD57tQmkyWzWY4a2QPe3xRxjoD2qnIX5YcGx_6kZ4ApClwri0BDVBfpFSZpSXtBemIxQYIu',
    "storageBucket": b'gAAAAABdY8TtKf93x7ZC7gj1nC2dRx1JghGY74-vHqZq0nXc9FH51fJjXDzOvUZKcQRSMteMjIIKshHBz8sx4n_BTlgdTP64LN4tG9-hWwaGBJ5KgLfOlZA=',
}

with open("shared_resources/encryption_key.json", 'rb') as f:
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

MSG_HEALTH_DIAGNOSTIC_IN = "HealthDiagnostic_in/"
MSG_HEALTH_DIAGNOSTIC_OUT = "HealthDiagnostic_out/"

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

## Health Diagnostic
HealthDiagnostic_subscribes = [MSG_HEALTH_DIAGNOSTIC_IN]
HealthDiagnostic_publishes = MSG_HEALTH_DIAGNOSTIC_OUT

####################################################################################################
##                                        Firebase Keys                                           ##
####################################################################################################

# High level keys
FIREBASE_KEY_USERS = "Users"
FIREBASE_KEY_SESSIONS = "Sessions"

# Shared / low level keys
FIREBASE_KEY_DATETIME = "datetime"
FIREBASE_KEY_CLIENTID = "client_id"
FIREBASE_KEY_ACKFOR = "for"

# Dialog keys
FIREBASE_KEY_DIALOG = "dialog"
FIREBASE_KEY_TEXT = "text"
FIREBASE_KEY_SOURCE = "source"
FIREBASE_VALUE_SOURCE_CLIENT = "client"
FIREBASE_VALUE_SOURCE_AGENT = "agent"
FIREBASE_KEY_ACK = "ack"
# Datacollection keys
FIREBASE_KEY_AMTID = "amt_id"
FIREBASE_KEY_DATACOLLECTION = "data_collection"
FIREBASE_KEY_FOOD_DIAGNOSIS_ANSWERS = "food_diagnosis_answers"


####################################################################################################
##                                          Modules                                               ##
####################################################################################################

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
            # self.NLU = None
            # self.DM = None
            # self.SentimentAnalysis = None
            # self.NLG = None
            # self.DataCollector = data_collection.DataCollector
            dataCollector_config = {"module": data_collection.DataCollector, "subscribes": DataCollector_subscribes, "publishes": DataCollector_publishes, "ack_msg": FIREBASE_KEY_ACK}
            self.modules = list()
            self.modules.append(dataCollector_config)

    def set_domain(self, domain):
        if domain == "movies":
            NLU_config = {"module": movies_NLU.RuleBasedNLU, "subscribes": NLU_subscribes, "publishes": NLU_publishes}
            DM_config = {"module": movies_DM.DM, "subscribes": DM_subscribes, "publishes": DM_publishes}
            NLG_config = {"module": movies_NLG.NLG, "subscribes": NLG_subscribes, "publishes": NLG_publishes}
            SA_config = {"module": movies_SA.SentimentAnalysis, "subscribes": SentimentAnalysis_subscribes, "publishes": SentimentAnalysis_publishes}
            self.modules += [NLU_config, DM_config, NLG_config, SA_config]
            logging.log.info("(config.py) Set domain as movies.")
        elif domain == "food":
            NLU_config = {"module": food_NLU.NLU, "subscribes": NLU_subscribes, "publishes": NLU_publishes}
            DM_config = {"module": food_DM.DM, "subscribes": DM_subscribes+[MSG_HEALTH_DIAGNOSTIC_OUT], "publishes": DM_publishes}
            NLG_config = {"module": food_NLG.NLG, "subscribes": NLG_subscribes, "publishes": NLG_publishes, "tags_explanation_types": EXPLANATION_TYPE}
            SA_config = {"module": movies_SA.SentimentAnalysis, "subscribes": SentimentAnalysis_subscribes, "publishes": SentimentAnalysis_publishes}
            HeathDiagnostic_config = {"module": heath_diagnostic.HealthDiagnostic, "subscribes": HealthDiagnostic_subscribes, "publishes": HealthDiagnostic_publishes}
            self.modules += [NLU_config, DM_config, NLG_config, SA_config, HeathDiagnostic_config]
            logging.log.info("(config.py) Set domain as food.")
        else:
            logging.log.error("No %s domain" % domain)
            exit(0)

modules = Modules.getInstance()



