import cryptography.fernet as fernet
import json

####################################################################################################
##                                              Voc                                               ##
####################################################################################################
# DM publishes on 2 channels
RECIPE_DM_MSG = "recipe_DM_msg" # should be used to send recipes to NLG so that NLS can fetch recipe cards in advance.
USUAL_DM_MSG = "usual_DM_msg" #should be used for everything else

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

user_name = "user_name"

food = "food"
food_type = "food_type"
food_name = "food_name"

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
title = "title"

# DM: user model
usual_dinner = "usual_dinner"
liked_features = "liked_features"
disliked_features = "disliked_features"
liked_food = "liked_food"
disliked_food = 'disliked_food'
liked_recipe = "liked_recipe"
disliked_recipe = "disliked_recipe"
special_diet = 'special_diet'
situation = "situation"
food_scores_trait = "food_scores_trait"
food_scores_state = "food_scores_state"

####################################################################################################
##                                          Resources Path                                        ##
####################################################################################################

DM_MODEL = "food/resources/dm/model.csv"
USER_MODELS = "food/resources/user_models/"
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
MAX_RECOMMENDATIONS = 5

EDAMAM_APP_ID = "&app_id=31e2abca"
EDAMAM_KEY = "&app_key=befbcff0d60f1af684f881c7f24ed296"
EDAMAM_SEARCH_RECIPE_ADDRESS = "https://api.edamam.com/search?q="
EDAMAM_PROPERTY = "&from=0&to=5&diet=low-fat"
EDAMAM_ADDITIONAL_DIET = ""
MOVIEDB_POSTER_PATH = "https://image.tmdb.org/t/p/original/"
# "https://api.edamam.com/search?q=chicken&app_id=${YOUR_APP_ID}&app_key=${YOUR_APP_KEY}&from=0&to=3&calories=591-722&health=alcohol-free"


SPOONACULAR_KEY = b'gAAAAABduryIrAaX-zsQLqzVjah6HXKrwA1GBGPCTNap8FyXniQKFw2uGJP8vxbcbut-WVUXnR3Emct7iMxXhKWQ15wUPlt2idUjNnxhiB9TF8pM9S12ev19M-2u40cGoE6Vxeb7duqR'
SPOONACULAR_API_SEARCH = "https://api.spoonacular.com/recipes/complexSearch?apiKey="
N_RESULTS = 5
SPOONACULAR_API_SEARCH_RESULTS_NUMBER = "&number=" + N_RESULTS.__str__()
SPOONACULAR_API_ADDITIONAL_INGREDIENTS = "&includeIngredients="
SPOONACULAR_API_MAX_TIME = "&maxReadyTime="
SPOONACULAR_API_DIET = "&diet="
SPOONACULAR_API_TYPE = "&type=main%20course"
SPOONACULAR_API_EXCLUDE_INGREDIENTS = "&excludeIngredients="
SPOONACULAR_API_INTOLERANCES = "&intolerances="
SPOONACULAR_API_SEARCH_ADDITIONAL_INFO = "&fillIngredients=true&addRecipeInformation=true"
SPOONACULAR_FOOD_RECO = "https://api.spoonacular.com/food/detect?apiKey="
SPOONACULAR_API_VISUALIZE = "https://api.spoonacular.com/recipes/visualizeRecipe?apiKey="
#https://api.spoonacular.com/recipes/complexSearch?apiKey=f124c11f97374e4ea23184db8d4f4097&query=pasta&maxFat=25&number=2&fillIngredients=true&addRecipeInformation=true

#title 	string 	My recipe 	The title of the recipe.
#image 	binary 		The binary image of the recipe as jpg.
#ingredients 	string 	2 cups of green beans 	The ingredient list of the recipe, one ingredient per line (separate lines with \n).
#instructions 	string 	cook the beans 	The instructions to make the recipe. One step per line (separate lines with \n).
#readyInMinutes 	number 	60 	The number of minutes it takes to get the recipe on the table.
#servings 	number 	2 	The number of servings the recipe makes.
#mask 	string 	ellipseMask 	The mask to put over the recipe image ("ellipseMask", "diamondMask", "starMask", "heartMask", "potMask", "fishMask").
#backgroundImage 	string 	background1 	The background image ("none","background1", or "background2").
#author 	string 	Anna Banana 	The author of the recipe.
#backgroundColor 	string 	#ffffff 	The background color for the recipe card as a hex-string.
#fontColor 	string 	#333333 	The font color for the recipe card as a hex-string.
#source 	string 	spoonacular.com 	The source of the recipe.


with open("shared_resources/encryption_key.json", 'rb') as f:
    key = json.load(f)["encryption_key"]
# print(key)
f = fernet.Fernet(key.encode())
SPOONACULAR_KEY = f.decrypt(SPOONACULAR_KEY).decode()
print("Spoonacular KEY ", SPOONACULAR_KEY)
