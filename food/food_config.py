
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
EDAMAM_ADDITIONAL_DIET = ""
MOVIEDB_POSTER_PATH = "https://image.tmdb.org/t/p/original/"
# "https://api.edamam.com/search?q=chicken&app_id=${YOUR_APP_ID}&app_key=${YOUR_APP_KEY}&from=0&to=3&calories=591-722&health=alcohol-free"


SPOONACULAR_KEY = "f124c11f97374e4ea23184db8d4f4097"
SPOONACULAR_API_SEARCH = "https://api.spoonacular.com/recipes/complexSearch?apiKey="
SPOONACULAR_API_SEARCH_RESULTS_NUMBER = "&number=2"
SPOONACULAR_API_SEARCH_ADDITIONAL_INFO = "&fillIngredients=true&addRecipeInformation=true"
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