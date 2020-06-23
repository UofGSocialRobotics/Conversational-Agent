import json
import csv
import copy
import spacy
from termcolor import colored

import food.resources.recipes_DB.allrecipes.nodejs_scrapper.consts as consts
import food.RS_utils as rs_utils
import food.food_dataparser as food_dataparser
import food.NLU as foodNLU
import nlu_helper_functions as nlu_helper
import helper_functions as helper
import dataparser

def create_json_10reviews():
    with open(consts.json_fullDB_path, 'r') as fjson:
        content = json.load(fjson)
    rdata = content['recipes_data']
    udata = content['users_data']
    rdata10 = dict()
    udata10 = dict()
    for rid, rdict in rdata.items():
        if rdict['reviews']['n_reviews_collected'] >= 10:
            rdata10[rid] = copy.copy(rdict['recipe_info'])
            rdata10[rid]['n_reviews'] = rdict['reviews']['n_reviews_collected']
            # print(rdata10[rid])
            del rdata10[rid]['n_ratings']
            rdata10[rid]['reviews'] = rdict['reviews']['reviews']
            sum_reviews = 0
            for review in rdata10[rid]['reviews']:
                # print(review)
                sum_reviews += int(review['rating'])
            rdata10[rid]['rating'] = float(sum_reviews) / len(rdata10[rid]['reviews'])
    for uid, udict in udata.items():
        # print(udict)
        if udict['n_comments'] >= 10:
            udata10[uid] = udict
    with open(consts.json_recipes_data_10reviews, 'w') as f:
        json.dump(rdata10, f, indent=True)
    with open(consts.json_users_data_10_reviews, 'w') as f:
        json.dump(udata10, f, indent=True)
    print("Wrote files:", consts.json_recipes_data_10reviews, consts.json_users_data_10_reviews)


def get_DB_numbers():
    with open(consts.json_reviews_file_path, 'r') as fjson:
        content = json.load(fjson)

    total_reviews = 0
    users = dict()
    for rid, ratings_data in content.items():
        total_reviews += ratings_data['n_reviews_collected']
        for review in ratings_data['reviews']:
            uid = review['id']
            if uid not in users.keys():
                users[uid] = 0
            users[uid] += 1

    print("Recipes:", len(content.keys()))
    print("Users:", len(users.keys()))
    print("Ratings:", total_reviews)


def get_matrix_data(users_comments_data, recipes_dict):
    n_reviews = 0
    for uid, udata in users_comments_data.items():
        n_reviews += udata['n_comments']

    n_recipes = len(recipes_dict.keys())
    n_users = len(users_comments_data.keys())
    print("Recipes:", n_recipes)
    print("Users:", n_users)
    print("Ratings:", n_reviews)
    print("Populated:", float(n_reviews) / (n_users * n_recipes))



def get_users_data():
    with open(consts.json_reviews_file_path, 'r') as fjson:
        content = json.load(fjson)

    users = dict()
    for rid, ratings_data in content.items():
        for review in ratings_data['reviews']:
            uid = review['id']
            if uid not in users.keys():
                users[uid] = dict()
                users[uid]['n_comments'] = 0
                users[uid]['recipes_commented'] = list()
            users[uid]['n_comments'] += 1
            users[uid]['recipes_commented'].append(rid)

    return users


def get_elts_with_X_or_more_ratings(elts_data, X=5, elt_name='users', key='n_comments'):
    elts = list()
    for elt, data in elts_data.items():
        x = data[key]
        if x >= X:
            elts.append(elt)
    print("%d %s with >= %d comments" % (len(elts), elt_name, X))
    return elts


def reduce_DB_size():

    with open(consts.json_users_data_10_reviews, 'r') as f_user_10:
        users_comments_data = json.load(f_user_10)

    with open(consts.json_recipes_data_10reviews, 'r') as f_recipe_10:
        recipes_dict = json.load(f_recipe_10)

    users_names = users_comments_data.keys()

    #eliminate users with less than 5 comments
    print("USERS")
    users_with_X_or_more_comments = get_elts_with_X_or_more_ratings(users_comments_data, consts.X_users)
    new_users_comments_data = dict()
    count = 0
    for user_id, user_data in users_comments_data.items():
        if user_id in users_with_X_or_more_comments:
            new_users_comments_data[user_id] = user_data
        count += 1
    users_comments_data = new_users_comments_data

    n_users, n_recipes = len(users_names), len(recipes_dict.keys())
    difference = -1

    while difference != 0:

        # eliminate comments in recipes from users with less than 5 comments
        print("RECIPES")
        new_recipes_dict = dict()
        count = 0
        for recipe_id, recipe in recipes_dict.items():
            new_comments_list = list()
            for review in recipe['reviews']:
                # print(review)
                if review['id'] in users_with_X_or_more_comments:
                    new_comments_list.append(review)
            recipe['reviews'] = new_comments_list
            recipe['n_reviews_collected'] = len(new_comments_list)
            if recipe['n_reviews_collected'] >= consts.X_recipes:
                new_recipes_dict[recipe_id] = recipe
            count += 1
        recipes_dict = new_recipes_dict

        #eliminate users
        recipes_with_X_or_more_comments = get_elts_with_X_or_more_ratings(recipes_dict, consts.X_recipes, 'recipes', 'n_reviews_collected')
        new_users_comments_data = dict()
        for user_id, user_data in users_comments_data.items():
            new_commented_recipes_list = list()
            # print(user_data['recipes_commented'])
            for r in user_data['recipes_commented']:
                if r in recipes_with_X_or_more_comments:
                    new_commented_recipes_list.append(r)
            user_data['n_comments'] = len(new_commented_recipes_list)
            user_data['recipes_commented'] = new_commented_recipes_list
            if user_data['n_comments'] >= consts.X_users:
                new_users_comments_data[user_id] = user_data

        users_comments_data = new_users_comments_data

        print("USERS")
        users_with_X_or_more_comments = get_elts_with_X_or_more_ratings(users_comments_data, consts.X_users)

        new_n_users, new_n_recipes = len(users_comments_data.keys()), len(recipes_dict.keys())
        difference = (n_users - new_n_users) + (n_recipes - new_n_recipes)
        n_users, n_recipes = new_n_users, new_n_recipes

        print(difference)

    get_matrix_data(users_comments_data, recipes_dict)

    json_data = dict()
    json_data['recipes_data'] = recipes_dict
    json_data['users_data'] = users_comments_data
    with open(consts.json_xUsers_Xrecipes_path, 'w') as fout:
        json.dump(json_data, fout, indent=True)


def create_user_item_matrix():
    with open(consts.json_xUsers_Xrecipes_path, 'r') as fin:
        content = json.load(fin)
    recipes_data = content['recipes_data']
    csv_rows = list()
    csv_rows.append(['item', 'user', 'rating'])
    number_of_x = dict()
    for recipe_id, recipe_data in recipes_data.items():
        reviews = recipe_data[consts.reviews]
        for review in reviews:
            user_id = review[consts.uid]
            rating = int(review[consts.rating])
            csv_rows.append([recipe_id, user_id, rating])
            if rating not in number_of_x.keys():
                number_of_x[rating] = 1
            else:
                number_of_x[rating] += 1
    total = len(csv_rows) - 1
    print("We collected %d ratings\n\nDistribution:" % total)
    for k, v in number_of_x.items():
        print("%d: %d (%.2f%%)" % (k, v, float(v)/total*100))

    path = consts.csv_xUsers_Xrecipes_path
    with open(path, 'w') as fout:
        writer = csv.writer(fout)
        for row in csv_rows:
            writer.writerow(row)

def save_FSAscore():
    with open(consts.json_xUsers_Xrecipes_path, 'r') as fjson:
        content = json.load(fjson)
    recipes_list = content['recipes_data'].values()
    for recipe in recipes_list:
        FSA_score = rs_utils.FSA_heathsclore(recipe)
        recipe['FSAscore'] = FSA_score
    # rid = list(content['recipes_data'].keys())[0]
    # r = content['recipes_data'][rid]
    # print(r)
    with open(consts.json_xUsers_Xrecipes_path, 'w') as fjson:
        json.dump(content, fjson, indent=True)
    print("Wrote Heath scores in", consts.json_xUsers_Xrecipes_path)


def json_list_dataset_rids():
    with open(consts.json_xUsers_Xrecipes_path, 'r') as fjson:
        content = json.load(fjson)
    rids_list = list(content['recipes_data'].keys())
    with open(consts.json_rids_list_xUsers_Xrecipes_path, 'w') as fout:
        json.dump(rids_list, fout, indent=True)


def merge_descriptions_to_main():
    with open(consts.json_descriptions_xUsers_Xrecipes_path, 'r') as fdescriptions:
        descriptions = json.load(fdescriptions)
    with open(consts.json_xUsers_Xrecipes_path, 'r') as fjson:
        content = json.load(fjson)
    recipes_data = content['recipes_data']
    for rid, rdata in recipes_data.items():
        if rid not in descriptions.keys():
            print("No description for %s" % rid)
        else:
            rdata['description'] = descriptions[rid]
    # first_rid = list(recipes_data.keys())[0]
    # first_rdtata = recipes_data[first_rid]
    # print(first_rdtata)
    content['recipes_data'] = recipes_data
    with open(consts.json_xUsers_Xrecipes_path, 'w') as fjson:
        json.dump(content, fjson, indent=True)


def tag_recipes_with_diet(verbose=True):
    with open(consts.json_xUsers_Xrecipes_path, 'r') as fjson:
        content = json.load(fjson)
    recipes_data = content["recipes_data"]

    with open(consts.json_xUsers_Xrecipes_withDiets_path, 'r') as f_parsed:
        json_parsed = json.load(f_parsed)
    rid_parsed = list(json_parsed["recipes_data"].keys())

    spacy_nlp = spacy.load("en_core_web_sm")
    voc = dataparser.parse_voc(f_domain_voc="food/resources/nlu/food_voc.json")
    food_list = food_dataparser.extensive_food_DBs.all_foods_list
    food_dict_category_to_food = food_dataparser.extensive_food_DBs.category_to_foods
    food_dict_food_to_category = food_dataparser.extensive_food_DBs.food_to_category
    print(food_dict_category_to_food.keys())
    print(food_dict_category_to_food['eggs'])

    ## overwrite categories
    food_dict_food_to_category["chicken"] = "meat"
    food_dict_food_to_category["butter"] = "dairy"
    food_dict_food_to_category["sauce"] = "unknown"
    food_dict_food_to_category["cream"] = "dairy"
    food_dict_food_to_category["potato"] = "vegetables"
    food_dict_food_to_category["meat"] = "meat"
    food_dict_food_to_category["cocoa"] = "cocoa"

    errors_dict = dict()

    ## Errors
    # 4 tablespoons chopped pecans ['butter'] ['cocoa']


    count, n_err = 0, 0
    new_recipes_data = dict()

    for rid, rdata in recipes_data.items():
        # print(rid)
        if rid in rid_parsed:
            count += 1
        else:
            error_bool, count, n_err, vegan, vegetarian, pescetarian, gluten_free, dairy_free, keto, low_carbs = parse_recipe(rid, rdata, count, n_err, spacy_nlp, food_list, food_dict_food_to_category, errors_dict, voc)

            if not error_bool:

                # print(rdata['nutrition'].keys())
                carbs_g_str = rdata["nutrition"]['nutrients']["Total Carbohydrates:"]
                if "g" in carbs_g_str:
                    carbs_g_str = carbs_g_str.replace("g", "")
                carbs_g = float(carbs_g_str)
                if carbs_g > 120:
                    low_carbs = False
                elif carbs_g > 40:
                    keto = False

                rdata["diets"] = dict()
                rdata["diets"]["vegan"] = vegan
                rdata["diets"]["vegetarian"] = vegetarian
                rdata["diets"]["pescetarian"] = pescetarian
                rdata["diets"]["gluten_free"] = gluten_free
                rdata["diets"]["dairy_free"] = dairy_free
                rdata["diets"]["keto"] = keto
                rdata["diets"]["low_carbs"] = low_carbs

                new_recipes_data[rid] = rdata

                # Standard ketogenic diet (SKD): This is a very low-carb, moderate-protein and high-fat diet. It typically contains 75% fat, 20% protein and only 5% carb
                # Ketogenic: less than 20 grams of net carbs per day
                # he exact number of grams (g) of carbohydrates will be different for everyone, but is generally around 20 to 50 g per day.
                # While 20 grams of total carbs is the amount that can get pretty much everyone into ketosis provided you eat within your daily macros, 20 grams of net carbs is the starting point for most people trying to achieve weight loss or general health benefits
                # Get 5-10% of your calories from carbs (typically under 50g net carbs per day)
                # here’s no strict definition of a low-carb, high-fat diet. Basically, low-carb is keto, but with slightly higher carb intake – maybe 75-150g of carbs a day.
                # The ketogenic diet typically reduces total carbohydrate intake to less than 50 grams a day—less than the amount found in a medium plain bagel—and can be as low as 20 grams a day.
                # Generally, popular ketogenic resources suggest an average of 70-80% fat from total daily calories, 5-10% carbohydrate, and 10-20% protein.
                # For a 2000-calorie diet, this translates to about 165 grams fat, 40 grams carbohydrate, and 75 grams protein

                if vegan == True:
                    print(colored("Vegan!", "blue"))
                print("vegan", vegan, " | vegetarian", vegetarian, " | pescetarian", pescetarian, " | glutenFree", gluten_free, " | dairyFree", dairy_free, " | keto", keto, " | lowCarbs", low_carbs)


            if count % 10 == 0:
                with open(consts.json_xUsers_Xrecipes_withDiets_path, 'w') as fjsonout:
                    content["recipes_data"] = new_recipes_data
                    json.dump(content, fjsonout, indent=True)
                    print(colored("Wrote to " + consts.json_xUsers_Xrecipes_withDiets_path, "yellow"))

            print("\n-------------\n")
            count += 1


def print_unparsed_ingredients(errors_dict, rid, ingredient, ingredients_parsed, categories):
    err = "Warning -----------------> "
    errors_dict[rid] = dict()
    errors_dict[rid]["ingredient"] = ingredient
    errors_dict[rid]["ingredients_parsed"] = ingredients_parsed
    errors_dict[rid]["categories"] = categories
    ingredients_categories_str = ", ".join(ingredients_parsed) + " --> " + ", ".join(categories) if ingredients_parsed else "? --> ?"
    err_str = err + ingredient + " --> " + ingredients_categories_str
    print(colored(err_str, "red"))


def parse_recipe(rid, rdata, count, n_err, spacy_nlp, food_list, food_dict_food_to_category, errors_dict, voc):

    print(count, "|", rdata['title'])

    error_bool, potential_error_bool = False, False
    all_categories, all_ingredients = list(), list()

    for ingredient in rdata["ingredients"]:
        # print(ingredient)
        utterance = ingredient.lower().strip()
        utterance = nlu_helper.preprocess(utterance)
        utterance = foodNLU.preprocess_foodNLU(utterance)
        document = spacy_nlp(utterance)
        res = foodNLU.inform_food(document, utterance, food_list, voc_no=voc["no"]["all_no_words"], voc_dislike=voc["dislike"])
        ingredients_parsed = None
        categories = list()
        if res:
            ingredients_parsed = res[2]
            # print(ingredients_parsed)
            for i in ingredients_parsed:
                categories.append(food_dict_food_to_category[i])
                if i not in all_ingredients:
                    all_ingredients.append(i)
            for elt in categories:
                if elt not in all_categories:
                    all_categories.append(elt)

        # error_bool = False
        if not ingredients_parsed:
            print_unparsed_ingredients(errors_dict, rid, ingredient, ingredients_parsed, categories)
            potential_error_bool = True
            # break


    # if not error_bool:
    print(all_categories)

    vegan, vegetarian, pescetarian, gluten_free, dairy_free, keto, low_carbs = True, True, True, True, True, True, True
    if "meat" in all_categories:
        vegan, vegetarian, pescetarian = False, False, False
    if "fish" in all_categories:
        vegan, vegetarian = False, False
    if "eggs" in all_categories:
        vegan = False
    if "dairy" in all_categories:
        vegan, dairy_free = False, False
    if "honey" in all_ingredients:
        vegan = False
    gluten_free_ingredients_to_avoid = [
        "wheat", "flour", "farina",
        "bread", "bagels", "biscuit", "cornbread", "flatbread", "naan", "pita", "rolls", "breadcrumbs", "croutons",
        "couscous", "bulgur", "barley", "rye", "gravy", "oat", "oats", "oatmeal",
        "soy sauce", "teriyaki sauce", "hoisin sauce", "beer",
        "crepes", "french toast", "pancakes", "waffles"
    ]
    if helper.any_elt_of_L1_in_L2(gluten_free_ingredients_to_avoid, all_ingredients):
        gluten_free = False
    if "pasta" in all_categories or "snack foods" in all_categories:
        gluten_free = False


    if ("unknown" in categories or "dishes" in categories or potential_error_bool):

        if ("unknown" in categories or "dishes" in categories):
            print(colored("Warning  ----------------->  unknown or dishes in categories...", "red"))

        if (vegan == True or vegetarian == True or pescetarian == True or gluten_free == True or dairy_free == True):
            n_err += 1
            print(colored("# errors = %d (%.2f%%)" % (n_err, float(n_err)/count*100), "red"))

            if n_err % 5 == 0:
                with open(consts.json_failedTagging_xUsers_Xrecipes_path, 'w') as fjson_errors:
                    json.dump(errors_dict, fjson_errors, indent=True)
                    print(colored("Wrote to " + consts.json_failedTagging_xUsers_Xrecipes_path, "yellow"))

            error_bool = True

        else:
            print(colored("Turns out we're good, all diets are already set to False!", "green"))

    return error_bool, count, n_err, vegan, vegetarian, pescetarian, gluten_free, dairy_free, keto, low_carbs


def check_vegan_recipes():
    with open(consts.json_xUsers_Xrecipes_withDiets_path, 'r') as fjsonin:
        content = json.load(fjsonin)
    recipes_data = content['recipes_data']
    for rid, rdata in recipes_data.items():
        if rdata["diets"]['vegan'] == True:
            print("\n----------")
            print(rdata['title'])
            for ingredient in rdata['ingredients']:
                print(ingredient)
            is_OK = input("Approve as vegan?")
            if is_OK == "n" or is_OK == "0":
                rdata["diets"]['vegan'] = False
    content['recipes_data'] = recipes_data
    with open(consts.json_xUsers_Xrecipes_withDiets_path, 'w') as fjsonout:
        json.dump(content, fjsonout, indent=True)


def manually_annotate_recipes():
    with open(consts.json_xUsers_Xrecipes_path, 'r') as f_parsed:
        content = json.load(f_parsed)
    recipes_data = content["recipes_data"]

    with open(consts.json_xUsers_Xrecipes_withDiets_path, 'r') as f_parsed:
        content_with_diets = json.load(f_parsed)
    recipes_data_with_diets = content_with_diets["recipes_data"]
    rids_recipes_with_diets = list(recipes_data_with_diets.keys())

    spacy_nlp = spacy.load("en_core_web_sm")
    voc = dataparser.parse_voc(f_domain_voc="food/resources/nlu/food_voc.json")
    food_list = food_dataparser.extensive_food_DBs.all_foods_list
    food_dict_category_to_food = food_dataparser.extensive_food_DBs.category_to_foods
    food_dict_food_to_category = food_dataparser.extensive_food_DBs.food_to_category

    ## overwrite categories
    food_dict_food_to_category["chicken"] = "meat"
    food_dict_food_to_category["butter"] = "dairy"
    food_dict_food_to_category["sauce"] = "unknown"
    food_dict_food_to_category["cream"] = "dairy"
    food_dict_food_to_category["potato"] = "vegetables"
    food_dict_food_to_category["meat"] = "meat"
    food_dict_food_to_category["cocoa"] = "cocoa"

    errors_dict = dict()
    count, n_err = 0, 0

    for rid, rdata in recipes_data.items():

        count += 1

        if rid not in rids_recipes_with_diets and 'diets' not in rdata.keys():

            error_bool, count, n_err, vegan, vegetarian, pescetarian, gluten_free, dairy_free, keto, low_carbs = parse_recipe(rid, rdata, count, n_err, spacy_nlp, food_list, food_dict_food_to_category, errors_dict, voc)
            print("error?", error_bool)

            if error_bool:

                for ingredient in rdata['ingredients']:
                    print(ingredient)

                rdata["diets"] = dict()
                check_with_user(rdata, vegan, "vegan")
                check_with_user(rdata, vegetarian, "vegetarian")
                check_with_user(rdata, pescetarian, "pescetarian")
                check_with_user(rdata, gluten_free, "gluten_free")
                check_with_user(rdata, dairy_free, "dairy_free")

                print("\n===============================\n")

                recipes_data[rid] = rdata

            else:
                rdata["diets"] = dict()
                rdata["diets"]["vegan"] = vegan
                rdata["diets"]["vegetarian"] = vegetarian
                rdata["diets"]["pescetarian"] = pescetarian
                rdata["diets"]["gluten_free"] = gluten_free
                rdata["diets"]["dairy_free"] = dairy_free
                rdata["diets"]["keto"] = keto
                rdata["diets"]["low_carbs"] = low_carbs

            recipes_data_with_diets[rid] = rdata
            content_with_diets['recipes_data'] = recipes_data_with_diets
            with open(consts.json_xUsers_Xrecipes_withDiets_path, 'w') as fjsonout:
                json.dump(content_with_diets, fjsonout, indent=True)



def check_with_user(rdata, var, label):
    if var == True:
        is_OK = input("Is it "+label+"? ")
        if is_OK == "n" or is_OK == "0":
            rdata["diets"][label] = False
        else:
            rdata["diets"][label] = True


def is_recipe_parsed_for_diets(title):

    with open(consts.json_xUsers_Xrecipes_withDiets_path, 'r') as f_parsed:
        json_parsed = json.load(f_parsed)
    parsed_recipes_data = json_parsed['recipes_data']
    for rid, rdata in parsed_recipes_data.items():
        if rdata['title'] == title:
            print("Found it!")
            return
    print("Did not find recipe")


if __name__ == "__main__":
    # create_json_10reviews()
    # reduce_DB_size()
    # create_user_item_matrix()
    # save_FSAscore()
    # json_list_dataset_rids()
    # merge_descriptions_to_main()
    # tag_recipes_with_diet()
    # check_vegan_recipes()
    # is_recipe_parsed_for_diets("Califo rnia Chicken")
    manually_annotate_recipes()
