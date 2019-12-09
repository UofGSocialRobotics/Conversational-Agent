import cryptography.fernet as fernet
import json



####################################################################################################
##                                       Experimental conditions                                  ##
####################################################################################################
exp_type_food = "food"
exp_type_opinion = "opinion"
exp_type_feature = "feature"
EXPLANATION_TYPE = [exp_type_food]

exp_cs_human = "human"
exp_cs_robot = "robot"
exp_cs_control = "NONE"
exp_no_ack = "no_ack"
aamas_study_CS = True
possible_CS = [exp_cs_human]


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
# print(key)
f = fernet.Fernet(key.encode())
for key, value in FIREBASE_CONFIG.items():
    FIREBASE_CONFIG[key] = f.decrypt(value).decode()

# Connection timeout, in secondes
CONNECTION_TIMEOUT = 60 * 15

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
MSG_DM_RECIPE_LIST = "DMrecipes/"
## For NLU, DM publishes on
MSG_DM_CONV_STATE = "DMstate/"

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
NLU_subscribes = [MSG_SERVER_IN, MSG_DM_CONV_STATE]
NLU_publishes = MSG_NLU

## DM
DM_subscribes = [MSG_NLU, MSG_SA]
DM_publishes = [MSG_DM, MSG_DM_RECIPE_LIST, MSG_DATACOL_IN, MSG_DATACOL_OUT, MSG_DM_CONV_STATE]

## NLG
NLG_subscribes = [MSG_DM, MSG_DM_RECIPE_LIST]
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
FIREBASE_KEY_DATA_RECO = "data_recommendation"
FIREBASE_KEY_XP_COND = "xp_condition"






