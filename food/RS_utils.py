import food.food_config as fc
import json

X_users = 8
X_recipes = 8
file_path = 'food/resources/recipes_DB/BBCGoodFood/without0ratings/recipes'+X_recipes.__str__()+'_users'+X_users.__str__()+'_DB.json'

healthy_reco_coverage_file_path = 'food/resources/recipes_DB/BBCGoodFood/without0ratings/coverage_Healthy_u'+X_users.__str__()+'r'+X_recipes.__str__()+'.txt'
CF_reco_coverage_file_path = 'food/resources/recipes_DB/BBCGoodFood/without0ratings/coverage_CFu'+X_users.__str__()+'r'+X_recipes.__str__()+'.txt'
CFhBias_coverage_file_path = 'food/resources/recipes_DB/CFHbias_reco_coverage.txt'


pref, hybrid, healthy, prefhybrid, prefhealthy, healthyhybrid, others, _all = 'pref', 'hybrid', 'healthy', 'pref+hybrid', 'pref+healthy', 'healthy+hybrid', 'others', 'all'
x, y, FSA_s, BBC_r, BBC_rc = 'x', 'y', 'FSA_score', 'bbc_rating', 'bbc_rating_count'
colors = dict()
colors[pref] = 'blue'
colors[healthy] = '#57E13D'
colors[others] = '#DEDFDF'
colors[prefhealthy] = 'orange'


def print_list_distribution(l):
    for elt in set(l):
        print(elt, l.count(elt))


def is_tagged_healthy(recipe):
    return "H" if 'Healthy' in recipe['additional_info'] else ""


def get_bbc_score(recipe):
    return float(recipe['ratings']['ratingValue'])

def get_bbc_rating_count(recipe):
    return float(recipe['ratings']['ratingCount'])

def WHO_heathscore(recipe):
    WHO_healthiness_score = 0
    for elt in fc.WHO_nutrition_elements:
        # print(recipe['nutrition'][elt])
        elt_quantity = float(recipe['nutrition'][elt].replace('g','') if 'g' in recipe['nutrition'][elt] else recipe['nutrition'][elt])
        if fc.WHO_RECOMMENDED_VALUES[elt][fc.unit] == 'grams':
            if elt_quantity >= fc.WHO_RECOMMENDED_VALUES[elt][fc.minumum] and elt_quantity <= fc.WHO_RECOMMENDED_VALUES[elt][fc.maximum]:
                WHO_healthiness_score += 1
        else:
            elt_cal = elt_quantity * fc.CALORIES_PER_GRAM[elt]
            percentage = elt_cal / float(recipe['nutrition']['kcal']) * 100
            # print(elt, elt_quantity, elt_cal, percentage)
            if percentage >= fc.WHO_RECOMMENDED_VALUES[elt][fc.minumum] and percentage <= fc.WHO_RECOMMENDED_VALUES[elt][fc.maximum]:
                WHO_healthiness_score += 1
    return WHO_healthiness_score


def FSA_heathsclore(recipe):
    FSA_healthiness_score = 0
    for elt in fc.FSA_nutrition_elements:
        if "-" in recipe['nutrition'][elt]:
            print("No nutrition values for %s" % recipe['id'])
            return -1
        # print(elt, recipe['nutrition'], recipe['nutrition'][elt])
        elt_quantity = float(recipe['nutrition'][elt].replace('g','') if 'g' in recipe['nutrition'][elt] else recipe['nutrition'][elt])
        if elt_quantity <= fc.FSA_RECOMMENDED_VALUES[elt][fc.low_to_medium]:
            FSA_healthiness_score += 1
        elif elt_quantity <= fc.FSA_RECOMMENDED_VALUES[elt][fc.medium_to_high]:
            FSA_healthiness_score += 2
        else:
            FSA_healthiness_score += 3
    return FSA_healthiness_score



def get_ids_healthy_recipes_coverage_set():
    # print("in get_ids_healthy_recipes_coverage_set")
    healthy_recipes_list = list()
    with open(healthy_reco_coverage_file_path, 'r') as healthy_reco_f:
        for line in healthy_reco_f:
            rid = line.split()[0]
            # print(line[:-1], rid)
            healthy_recipes_list.append(rid)
    return healthy_recipes_list


def get_ids_CFhBias_recipes_coverage_set():
    recipes_list = list()
    with open(CFhBias_coverage_file_path, 'r') as f:
        for line in f:
            recipes_list.append(line[9:].split()[0])
    return recipes_list

def get_ids_recipes_CF_coverage_set():
    CF_recipes_list = list()
    with open(CF_reco_coverage_file_path, 'r') as CF_reco_f:
        for line in CF_reco_f:
            CF_recipes_list.append(line[9:-1])
    return CF_recipes_list



def diff_list(l1, l2):
    res = list()
    for elt in l1:
        if l2 and elt in l2:
            l2.remove(elt)
        else:
            res.append(elt)
    if l2:
        raise ValueError("Some elements of list to substract are not included in main list!")
    return res