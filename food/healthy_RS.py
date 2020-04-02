import food.food_config as fc
import spacy
import food.food_dataparser as food_dataparser
import dataparser
import json
import nlu_helper_functions as nlu_helper
import food.NLU as NLU
import random
from food.RS_utils import *



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


def recipe_DB_heathscores_analysis():
    with open(file_path, 'r') as fjson:
        content = json.load(fjson)

    recipes_hs_list = list()

    count_scores = dict()
    
    for recipe in content['recipes_data'].values():
        # FSA_heathsclore(recipe)
        h = is_tagged_healthy(recipe)
        FSA_HS = FSA_heathsclore(recipe)
        if FSA_HS < 7 and FSA_HS != -1:
            recipes_hs_list.append([recipe['id'][9:], FSA_HS])
            print(recipe['id'], FSA_HS)

        if FSA_HS not in count_scores.keys():
            count_scores[FSA_HS] = dict()
            count_scores[FSA_HS]['total'] = 0
            count_scores[FSA_HS]['H_tag'] = 0
        count_scores[FSA_HS]['total'] += 1
        if h:
            count_scores[FSA_HS]['H_tag'] += 1

    for k, v in count_scores.items():
        print(k, v['total'], v['H_tag'])

    # print("-----")
    #
    # random.shuffle(recipes_hs_list)
    # recipes_hs_list = list(sorted(recipes_hs_list, key=lambda x: x[1]))
    # print(len(recipes_hs_list))
    # for x in recipes_hs_list:
    #     print(x[0], x[1])

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



if __name__ == "__main__":
    recipe_DB_heathscores_analysis()
    # compare_coverage_sets_healthy_reco_vs_CF_reco()
    # get_reco()
