import food.food_config as fc
import spacy
import food.food_dataparser as food_dataparser
import dataparser
import json
import nlu_helper_functions as nlu_helper
import food.NLU as NLU
import random
from food.RS_utils import *
import matplotlib.pyplot as plt

import food.resources.recipes_DB.allrecipes.nodejs_scrapper.consts as consts



def ingredients_healthscores_analysis(print_unparsed_ingredients=False):
    ingredients_found = list()
    spacy_nlp = spacy.load("en_core_web_sm")

    food_list = food_dataparser.extensive_food_DBs.all_foods_list
    voc = dataparser.parse_voc(f_domain_voc="food/resources/nlu/food_voc.json")
    total, correctely_parsed = 0, 0
    all_ingredients = dict()

    with open('food/resources/dm/bbcgoodfood_scraped_recipes.json', 'r') as f:
        content = json.load(f)
        for recipe in content:
            # parsing ingredients
            for ingredient in recipe['ingredients']:
                total += 1
                ingredients_found_in_ingredient_string = list()
                document = spacy_nlp(ingredient)
                if 'stock' in ingredient:
                    ingredients_found_in_ingredient_string.append('stock')
                elif 'oil' in ingredient:
                    ingredients_found_in_ingredient_string.append('oil')
                else:
                    utterance = nlu_helper.preprocess(ingredient)
                    utterance = NLU.preprocess_foodNLU(utterance)
                    NLU_ingredients = NLU.inform_food(document, utterance, food_list, voc_no=voc["no"]["all_no_words"], voc_dislike=voc["dislike"], threshold=100)
                    if NLU_ingredients:
                        ingredients_found_in_ingredient_string += NLU_ingredients[2]
                    list_of_words = ingredient.split() if " " in ingredient else ingredient
                    # if "pasta" not in ingredients_found_in_ingredient_string:
                    #     for w in list_of_words:
                    #         if w in voc['pasta']:
                    #             ingredients_found_in_ingredient_string.append(w)
                # to eliminate duplicates
                ingredients_found_in_ingredient_string = list(set(ingredients_found_in_ingredient_string))
                if len(ingredients_found_in_ingredient_string) != 1:
                    if ("cloves" in ingredients_found_in_ingredient_string or "juice" in ingredients_found_in_ingredient_string or "sauce" in ingredients_found_in_ingredient_string or 'ketchup' in ingredients_found_in_ingredient_string) and len(ingredients_found_in_ingredient_string) == 2 :
                        ingredients_found_in_ingredient_string = [" ".join(ingredients_found_in_ingredient_string)]
                if len(ingredients_found_in_ingredient_string) != 1:
                    extact_matches = list()
                    if ingredients_found_in_ingredient_string:
                        for i in ingredients_found_in_ingredient_string:
                            i_in_other_parsed_ingredient = False
                            for j in ingredients_found_in_ingredient_string:
                                if i != j and i in j:
                                    i_in_other_parsed_ingredient = True
                            if not i_in_other_parsed_ingredient and i in ingredient:
                                extact_matches.append(i)
                    ingredients_found_in_ingredient_string = extact_matches
                if print_unparsed_ingredients and len(ingredients_found_in_ingredient_string) != 1:
                    print(ingredient)
                    print(", ".join(ingredients_found_in_ingredient_string))
                else:
                    for i in ingredients_found_in_ingredient_string:
                        if i not in food_dataparser.extensive_food_DBs.food_to_category.keys():
                            ingredient_category = 'unknown'
                        else:
                            ingredient_category = food_dataparser.extensive_food_DBs.food_to_category[i]
                        if ingredient_category not in all_ingredients.keys():
                            all_ingredients[ingredient_category] = dict()
                        if i in all_ingredients[ingredient_category].keys():
                            all_ingredients[ingredient_category][i] += 1
                        else:
                            all_ingredients[ingredient_category][i] = 1
                    correctely_parsed += 1

    print("Ingredients successfully parsed: %.2f" % (float(correctely_parsed) / total))

    for category, ingredients_dict in all_ingredients.items():
        if category in ['dishes', 'unknown', 'dairy', 'vegetables', 'meat', 'eggs', 'gourds', 'pasta', 'fish']:
            print("\n---------------")
            print(category)
            for ingredient, found_in_n_recipes in ingredients_dict.items():
                print(ingredient, found_in_n_recipes)


def recipe_DB_heathscores_analysis(recipes_subsets_ids_list=False):
    with open(consts.json_xUsers_Xrecipes_path, 'r') as fjson:
        content = json.load(fjson)

    recipes_list = list()
    if not recipes_subsets_ids_list:
        recipes_list = content['recipes_data'].values()
    else:
        for rid in recipes_subsets_ids_list:
            recipes_list.append(content['recipes_data'][rid])

    count_scores = dict()

    n_recipes = len(recipes_list)

    x_green, x_amber, x_red = list(), list(), list()
    y_green, y_amber, y_red = list(), list(), list()
    
    for recipe in recipes_list:
        FSA_HS = recipe['FSAscore']

        if FSA_HS not in count_scores.keys():
            count_scores[FSA_HS] = dict()
            count_scores[FSA_HS]['total'] = 0
        count_scores[FSA_HS]['total'] += 1

        if FSA_HS < 7:
            x_green.append(recipe['n_reviews'])
            y_green.append(recipe['rating'])
        elif FSA_HS < 9:
            x_red.append(recipe['n_reviews'])
            y_red.append(recipe['rating'])
        else:
            x_amber.append(recipe['n_reviews'])
            y_amber.append(recipe['rating'])

    print("%d recipes" % n_recipes)

    A, B, x, A_colors, B_colors = list(), list(), list(), list(), list()

    count_scores_FSA_categories = dict()
    count_scores_FSA_categories["green"], count_scores_FSA_categories["amber"], count_scores_FSA_categories["red"] = 0, 0, 0

    for k, v in count_scores.items():
        v = v['total']
        A.append(v)
        x.append(k)
        if k < 7:
            A_colors.append(color_FSA_green)
            count_scores_FSA_categories["green"] += v
        elif k > 9:
            A_colors.append(color_FSA_red)
            count_scores_FSA_categories["red"] += v
        else:
            A_colors.append(color_FSA_amber)
            count_scores_FSA_categories["amber"] += v
        print("Health score = %d, n recipes = %d (%.2f%%)" % (k, v, float(v)/n_recipes*100))

    print("-----")

    for k, v in count_scores_FSA_categories.items():
        print("FSA category %s, n recipes = %d (%.2f%%)" % (k, v, float(v)/n_recipes*100))

    fig, (ax1, ax2) = plt.subplots(1, 2)
    fig.suptitle('FSA scores for dataset')

    ax1.bar(x, A, color=A_colors)
    ax1.set_xlabel("FSA score")
    ax1.set_ylabel("Number of recipes")
    # ax1.set_title("Distribution of recipes by FSA healthscore\nfor whole DB")
    # ax1.legend(numpoints=1)

    ax2.scatter(x_amber, y_amber, color=color_FSA_amber)
    ax2.scatter(x_red, y_red, color=color_FSA_red)
    ax2.scatter(x_green, y_green, color=color_FSA_green)
    ax2.set_xlabel("N ratings")
    ax2.set_ylabel("Rating")

    plt.show()


def get_reco():
    healthy_recipes = get_ids_healthy_recipes_coverage_set()
    random.shuffle(healthy_recipes)
    reco = healthy_recipes[:6]
    for r in reco:
        print(r)
    return reco


def compare_coverage_sets_healthy_reco_vs_CF_reco():
    healthy_recipes_list, CF_recipes_list = get_ids_healthy_recipes_coverage_set(), get_ids_recipes_CF_coverage_set()
    intersection = list(set(healthy_recipes_list) & set(CF_recipes_list))
    for elt in intersection:
        print(elt)

def save_coverage_healthRS():
    with open(consts.json_xUsers_Xrecipes_path, 'r') as fjson:
        content = json.load(fjson)
    all_lines = list()
    for rid, rdata in content['recipes_data'].items():
        if rdata['FSAscore'] < 7:
            all_lines.append(rid)
    outF = open(consts.txt_coverageHealth, "w")
    for line in all_lines:
        outF.write(line)
        outF.write("\n")
    outF.close()



if __name__ == "__main__":
    # rids = get_ids_recipes_CF_coverage_set()
    # rids = ["/recipes/" + rid for rid in rids]
    # print(rids)
    # recipe_DB_heathscores_analysis()
    # compare_coverage_sets_healthy_reco_vs_CF_reco()
    # get_reco()
    save_coverage_healthRS()
