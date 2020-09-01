import cryptography.fernet as fernet
import json


####################################################################################################
##                                              Voc                                               ##
####################################################################################################
# DM publishes on 2 channels
RECIPE_DM_MSG = "recipe_DM_msg" # should be used to send recipes to NLG so that NLS can fetch recipe cards in advance.
USUAL_DM_MSG = "usual_DM_msg" #should be used for everything else

normed_health_score = "normed_health_score"
normed_fillingness_score = "normed_fillingness_score"
health_score_distance_to_user_s_health_value = "distance_healthiness"
fillingness_score_distance_to_user_s_fillingness_value = "distance_fillingness"
average_health_fillingness_distance = "average_health_fillingness_distance"

intent = 'intent'
previous_intent = "previous_intent"
current_intent = "current_intent"
current_intent_should_not_be = "current_intent_should_not_be"
current_intent_should_be = "current_intent_should_be"
valence = "valence"
cs = 'cs'
tags = 'tags'
entity = "entity"
entity_type = "entity_type"
polarity = "polarity"
inform = "inform"

reco_mode = 'reco_mode'
reco_mode_pref = "reco_mode_pref"
reco_mode_healthier = "reco_mode_healthier"
reco_mode_utlra_healthy = "reco_mode_utlra_healthy"

user_name = "user_name"

food = "food"
diet = "diet"
food_type = "food_type"
food_name = "food_name"

# messages / topics for DM to RS messages
set_user_profile = "set_user_profile"
get_reco = "get_reco"
# messages / topics for RS to DM messages
reco_recipes = "reco_recipes"

recipes_list = "recipes_list"
reco_list = 'reco_list'

# keys words used by NLU
yes = 'yes'
no = 'no'
healthy = "healthy"
health = 'health'
not_healthy = 'not_healthy'
time = 'time'
no_time = 'no_time'
time_to_cook = "time_to_cook"
duration = 'duration'
hungry = 'hungry'
cuisine = 'cuisine'
not_hungry = 'not_hungry'
vegan = "vegan"
intolerances = "intolerances"
greeting = "greeting"
inform_food = "inform(food)"
comfort = "comfort"
filling = "filling"
request = "request"
more = "more"

# food diamensions (larry)
emotional_satisfaction = 'emotional_satisfaction'
healthiness = "healthiness"
food_fillingness = "food_fillingness"

# Food options
meal = 'meal'
dessert = 'dessert'
drink = 'drink'
meat = 'meat'
side = 'side'
main = 'main'
secondary = "secondary"
other_main = "other_main"

# Frame
user_intent = 'user_intent'
previous_intent = 'previous_intent'
user_model = 'user_model'
reco_food = 'reco_food'
recipe = 'recipe'
recipes = 'recipes'
title = "title"
ingredients = "ingredients"

# DM: user model
usual_dinner = "usual_dinner"
liked_features = "liked_features"
disliked_features = "disliked_features"
liked_food = "liked_food"
disliked_food = 'disliked_food'
liked_cuisine = "liked_cuisine"
disliked_cuisine = "disliked_cuisine"
liked_recipe = "liked_recipe"
disliked_recipe = "disliked_recipe"
# special_diet = 'special_diet'
situation = "situation"
food_scores_trait = "food_scores_trait"
food_scores_state = "food_scores_state"

salt = "Sodium:"
sugars = 'Sugars:'
fat = 'Total Fat:'
saturates = 'Saturated Fat:'
FSA_nutrition_elements = [salt, sugars, fat, saturates]
protein = "protein"
carbs = 'carbs'
fibre = 'fibre'
WHO_nutrition_elements = [salt, sugars, fat, saturates, protein, carbs, fibre]
low_to_medium = 'low-to-medium'
medium_to_high = 'medium-to-high'


####################################################################################################
##                                       Recommended food values                                  ##
####################################################################################################

# recommended values in grams
FSA_RECOMMENDED_VALUES = dict()
FSA_RECOMMENDED_VALUES[salt] = dict()
FSA_RECOMMENDED_VALUES[salt][low_to_medium] = 0.36
FSA_RECOMMENDED_VALUES[salt][medium_to_high] = 1.8
FSA_RECOMMENDED_VALUES[sugars] = dict()
FSA_RECOMMENDED_VALUES[sugars][low_to_medium] = 6
FSA_RECOMMENDED_VALUES[sugars][medium_to_high] = 27
FSA_RECOMMENDED_VALUES[fat] = dict()
FSA_RECOMMENDED_VALUES[fat][low_to_medium] = 3.6
FSA_RECOMMENDED_VALUES[fat][medium_to_high] = 21
FSA_RECOMMENDED_VALUES[saturates] = dict()
FSA_RECOMMENDED_VALUES[saturates][low_to_medium] = 1.25
FSA_RECOMMENDED_VALUES[saturates][medium_to_high] = 6

minumum = 'min'
maximum = 'max'
# recommended values in percentage of kcal per meal/recipe
grams = 'grams'
percentage_of_kcal = 'percentage_of_kcal'
unit = 'unit'
WHO_RECOMMENDED_VALUES = dict()
WHO_RECOMMENDED_VALUES[protein] = dict()
WHO_RECOMMENDED_VALUES[protein][unit] = percentage_of_kcal
WHO_RECOMMENDED_VALUES[protein][minumum] = 10
WHO_RECOMMENDED_VALUES[protein][maximum] = 15
WHO_RECOMMENDED_VALUES[carbs] = dict()
WHO_RECOMMENDED_VALUES[carbs][unit] = percentage_of_kcal
WHO_RECOMMENDED_VALUES[carbs][minumum] = 55
WHO_RECOMMENDED_VALUES[carbs][maximum] = 75
WHO_RECOMMENDED_VALUES[sugars] = dict()
WHO_RECOMMENDED_VALUES[sugars][unit] = percentage_of_kcal
WHO_RECOMMENDED_VALUES[sugars][minumum] = 0
WHO_RECOMMENDED_VALUES[sugars][maximum] = 10
WHO_RECOMMENDED_VALUES[fat] = dict()
WHO_RECOMMENDED_VALUES[fat][unit] = percentage_of_kcal
WHO_RECOMMENDED_VALUES[fat][minumum] = 15
WHO_RECOMMENDED_VALUES[fat][maximum] = 30
WHO_RECOMMENDED_VALUES[saturates] = dict()
WHO_RECOMMENDED_VALUES[saturates][unit] = percentage_of_kcal
WHO_RECOMMENDED_VALUES[saturates][minumum] = 0
WHO_RECOMMENDED_VALUES[saturates][maximum] = 10
WHO_RECOMMENDED_VALUES[fibre] = dict()
WHO_RECOMMENDED_VALUES[fibre][unit] = grams
WHO_RECOMMENDED_VALUES[fibre][minumum] = 25
WHO_RECOMMENDED_VALUES[fibre][maximum] = 10
WHO_RECOMMENDED_VALUES[salt] = dict()
WHO_RECOMMENDED_VALUES[salt][unit] = grams
WHO_RECOMMENDED_VALUES[salt][minumum] = 0
WHO_RECOMMENDED_VALUES[salt][maximum] = 0.6

CALORIES_PER_GRAM = dict()
CALORIES_PER_GRAM[fat] = 9
CALORIES_PER_GRAM[saturates] = 9
CALORIES_PER_GRAM[carbs] = 4
CALORIES_PER_GRAM[protein] = 4
CALORIES_PER_GRAM[sugars] = 4

rid = "recipe_id"
uid = 'user_id'
rating = "rating"
reco = "recommendation"



####################################################################################################
##                                          Resources Path                                        ##
####################################################################################################

DM_MODEL = "food/resources/dm/model.csv"
USER_MODELS = "food/resources/user_models/"
NLG_SENTENCE_DB = "food/resources/nlg/sentence_db.csv"
if "nosmalltalk" in DM_MODEL:
    NLG_SENTENCE_DB = "food/resources/nlg/sentence_db_nosmalltalk.csv"
NLG_ACK_DB = "food/resources/nlg/ack_db.csv"
# NLG_ACK_DB = "food/resources/nlg/ack_db.json"
FOOD_MODEL_PATH = "food/resources/dm/food_model.csv"
LOCAL_FOOD_DB = "food/resources/dm/recipes.json"
EXTENSIVE_FOOD_DB_PATH = "food/resources/nlu/foods.csv"
ADDITINAL_FOODS_DB_PATH = "food/resources/nlu/additions_to_food_DB.csv"

####################################################################################################
##                                          Other config                                          ##
####################################################################################################
SAVE_USER_MODEL = True
NLG_USE_ACKS = True
NLG_USE_ACKS_CS = True
NLG_USE_CS = True
NLG_USE_EXPLANATIONS = False
CS_LABELS = ["SD", "PR", "HE", "VSN", "NONE", 'QESD']
MAX_RECOMMENDATIONS = 1

EDAMAM_APP_ID = "&app_id=31e2abca"
EDAMAM_KEY = "&app_key=befbcff0d60f1af684f881c7f24ed296"
EDAMAM_SEARCH_RECIPE_ADDRESS = "https://api.edamam.com/search?q="
EDAMAM_PROPERTY = "&from=0&to=5&diet=low-fat"
EDAMAM_ADDITIONAL_DIET = ""
MOVIEDB_POSTER_PATH = "https://image.tmdb.org/t/p/original/"
# "https://api.edamam.com/search?q=chicken&app_id=${YOUR_APP_ID}&app_key=${YOUR_APP_KEY}&from=0&to=3&calories=591-722&health=alcohol-free"

