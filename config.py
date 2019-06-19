import movies
import food

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
ADDRESS = "mqtt.eclipse.org" #iot.eclipse.org
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
#import dum_NLU
#NLU = dum_NLU.NLU
import rule_based_NLU
NLU = rule_based_NLU.RuleBasedNLU
NLU_subscribes = [MSG_SERVER_IN]
NLU_publishes = MSG_NLU

## DM
from movies import DM, NLG, dum_sentiment_analysis
from food import DM

DM = food.DM.DM
DM_subscribes = [MSG_NLU, MSG_SA]
DM_publishes = MSG_DM

## NLG
NLG = movies.NLG.NLG
NLG_subscribes = [MSG_DM]
NLG_publishes = MSG_NLG

## Sentiment analysis
SentimentAnalysis = movies.dum_sentiment_analysis.SentimentAnalysis
SentimentAnalysis_subscribes = [MSG_SERVER_IN]
SentimentAnalysis_publishes = MSG_SA


####################################################################################################
##                                          Resources Path                                        ##
####################################################################################################

DM_MODEL = "./movies/resources/dm/Model.csv"
USER_MODELS = "./movies/resources/user_models/"
NLG_SENTENCE_DB = "./movies/resources/nlg/sentence_db.csv"
NLG_ACK_DB = "./movies/resources/nlg/ack_db.csv"
ACTORS_LEXICON = "./movies/resources/nlu/actor2id.lexicon"
DIRECTORS_LEXICON = "./movies/resources/nlu/director2id.lexicon"
GENRES_LEXICON = "./movies/resources/nlu/genre2id.lexicon"


####################################################################################################
##                                      Movie recommendation config                               ##
####################################################################################################
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
NLG_USE_ACKS = True
NLG_USE_ACKS_CS = True
NLG_USE_CS = True
NLG_USE_EXPLANATIONS = True
CS_LABELS = ["SD", "PR", "HE", "VSN", "NONE", 'QESD']
EXPLANATION_TYPE_LABELS = ["MF", "TPO", "PO", "PE"]
EXPLANATION_TYPE_PROBA = [.37, .07, .39, .17]
MF_EXPLANATION_LABELS = ["C", "G", "P", "A", "O"]
MF_EXPLANATION_PROBA = [.108, .243, .459, .055, .135]
TPO_EXPLANATION_LABELS = ["B", "S"]
TPO_EXPLANATION_PROBA = [.571, .429]
PO_EXPLANATION_LABELS = ["POS", "ANA", "SO"]
PO_EXPLANATION_PROBA = [.513, .308, .179]
PE_EXPLANATION_LABELS = ["A", "L", "C"]
PE_EXPLANATION_PROBA = [.177, .529, .294]




#####################################################################################################
#####################################################################################################
#####################################################################################################
#####################################################################################################
##########                                      FOOD PROJECT                            #############
#####################################################################################################
#####################################################################################################
#####################################################################################################
#####################################################################################################

FOOD_MODEL_PATH = "./food/resources/dm/food_ratings.csv"