
####################################################################################################
##                                          Resources Path                                        ##
####################################################################################################

DM_MODEL = "food/resources/dm/model.csv"
USER_MODELS = "food/resources/user_models/"
NLG_SENTENCE_DB = "food/resources/nlg/sentence_db.csv"
NLG_ACK_DB = "food/resources/nlg/ack_db.csv"
FOOD_MODEL_PATH = "food/resources/dm/food_model.csv"


####################################################################################################
##                                          Other config                                          ##
####################################################################################################
SAVE_USER_MODEL = True
NLG_USE_ACKS = True
NLG_USE_ACKS_CS = True
NLG_USE_CS = True
NLG_USE_EXPLANATIONS = False
CS_LABELS = ["SD", "PR", "HE", "VSN", "NONE", 'QESD']

EDAMAM_APP_ID = "&app_id=31e2abca"
EDAMAM_KEY = "&app_key=befbcff0d60f1af684f881c7f24ed296"
EDAMAM_SEARCH_RECIPE_ADDRESS = "https://api.edamam.com/search?q="
EDAMAM_PROPERTY = "&from=0&to=5&diet=low-fat"
MOVIEDB_POSTER_PATH = "https://image.tmdb.org/t/p/original/"
# "https://api.edamam.com/search?q=chicken&app_id=${YOUR_APP_ID}&app_key=${YOUR_APP_KEY}&from=0&to=3&calories=591-722&health=alcohol-free"