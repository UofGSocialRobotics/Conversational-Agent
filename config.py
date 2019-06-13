####################################################################################################
##                                Using broker or websockets on localhost                         ##
####################################################################################################

BROKER = "broker"
WEBSOCKETS = "websokects"
# USING = BROKER
USING = WEBSOCKETS

####################################################################################################
##                                        Broker config                                           ##
####################################################################################################
ADDRESS = "mqtt.eclipse.org" #"iot.eclipse.org"
PORT = 1883

# Connection timeout, in secondes
CONNECTION_TIMEOUT = 60 * 10


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

# Connection message from client:
MSG_CONNECTION = "new client connected"

# Confirm connection to client:
MSG_CONFIRM_CONNECTION = "Connection confirmed"


####################################################################################################
##                                          Modules                                               ##
####################################################################################################

## NLU
import dum_NLU
NLU = dum_NLU.NLU
#import rule_based_NLU
#NLU = rule_based_NLU.RuleBasedNLU
NLU_subscribes = [MSG_SERVER_IN]
NLU_publishes = MSG_NLU

## DM
import DM
import dum_DM
DM = DM.DM
DM_subscribes = [MSG_NLU, MSG_SA]
DM_publishes = MSG_DM

## NLG
import dum_NLG
import NLG
NLG = NLG.NLG
NLG_subscribes = [MSG_DM]
NLG_publishes = MSG_NLG

## Sentiment analysis
import dum_sentiment_analysis
SentimentAnalysis = dum_sentiment_analysis.SentimentAnalysis
SentimentAnalysis_subscribes = [MSG_SERVER_IN]
SentimentAnalysis_publishes = MSG_SA


####################################################################################################
##                                          Resources Path                                        ##
####################################################################################################

DM_MODEL = "./resources/dm/Model.csv"
USER_MODELS = "./resources/user_models/"
NLG_SENTENCE_DB = "./resources/nlg/sentence_db.csv"
NLG_ACK_DB = "./resources/nlg/ack_db.csv"

MOVIEDB_KEY = "6e3c2d4a2501c86cd7e0571ada291f55"
MOVIEDB_SEARCH_MOVIE_ADDRESS = "https://api.themoviedb.org/3/discover/movie?api_key="
MOVIE_DB_PROPERTY = "&sort_by=popularity.desc"
MOVIEDB_SEARCH_PERSON_ADDRESS = "https://api.themoviedb.org/3/search/person?api_key="
MOVIEDB_POSTER_PATH = "https://image.tmdb.org/t/p/original/"
OMDB_SEARCH_MOVIE_INFO = "http://www.omdbapi.com/?t="
OMDB_KEY = "be72fd68"
HIGH_QUALITY_POSTER = True

####################################################################################################
##                                          Other config                                          ##
####################################################################################################
SAVE_USER_MODEL = False
CS_LABELS = ["SD", "PR", "HE", "VSN", "NONE", 'QESD']
