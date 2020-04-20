import food.food_config as fc
import json
import statistics as stats
import re

X_users = 7
X_recipes = 10
file_path = 'food/resources/recipes_DB/BBCGoodFood/without0ratings/recipes'+X_recipes.__str__()+'_users'+X_users.__str__()+'_DB.json'

healthy_reco_coverage_file_path = 'food/resources/recipes_DB/BBCGoodFood/without0ratings/coverage_Healthy_u'+X_users.__str__()+'r'+X_recipes.__str__()+'.txt'
CF_reco_coverage_file_path = 'food/resources/recipes_DB/BBCGoodFood/without0ratings/coverage_CFu'+X_users.__str__()+'r'+X_recipes.__str__()+'_pretrained.txt'
CFhBias_coverage_file_path = 'food/resources/recipes_DB/BBCGoodFood/without0ratings/coverage_Hybrid_FSAcategories_u'+X_users.__str__()+'r'+X_recipes.__str__()+'_5outof10.txt'

coef_pref = 1
coef_healthy = 1

n_reco = 5
from_n_best = 10

n_alogs = 10
n_recipes_before_reco = 10

pref, hybrid, healthy, prefhybrid, prefhealthy, healthyhybrid, others, _all = 'pref', 'hybrid', 'healthy', 'pref+hybrid', 'pref+healthy', 'healthy+hybrid', 'others', 'all'
x, y, FSA_s, BBC_r, BBC_rc = 'x', 'y', 'FSA_score', 'bbc_rating', 'bbc_rating_count'
colors = dict()
colors[pref] = 'blue'
colors[healthy] = '#57E13D'
colors[hybrid] = '#3DE1CD'
colors[others] = '#DEDFDF'
colors[prefhealthy] = 'orange'
colors[prefhybrid] = 'red'
colors[healthyhybrid] = '#EBE400'
colors[_all] = '#FFFFFF'

color_FSA_green = "#11BF00"
color_FSA_green_h_tag = "#9AE992"
color_FSA_amber = "#FD8A1E"
color_FSA_amber_h_tag = "#FFC38A"
color_FSA_red = "#FE2C2C"
color_FSA_red_h_tag = "#FC8F8F"


svd_n_factors, svd_n_epochs, svd_lr_all, svd_reg_all = False, False, False, False
if X_users == 7 and X_recipes == 10:
    svd_n_factors, svd_n_epochs, svd_lr_all, svd_reg_all = 15, 30, 0.003, 0.3
    svd_best_RMSE_name = 'SVD-15-30-0.003-0.3-bestRMSE'
elif X_users == 8 and X_recipes == 10:
    svd_n_factors, svd_n_epochs, svd_lr_all, svd_reg_all = 4, 24, 0.004, 0.06
elif X_users == 8 and X_recipes == 8:
    svd_n_factors, svd_n_epochs, svd_lr_all, svd_reg_all = 10, 35, 0.003, 0.3
else:
    raise ValueError("Don's know any parameters for SVD with n users = %d and n recipes = %d" % (X_users, X_recipes))


def print_list_distribution(l):
    for elt in set(l):
        print(elt, l.count(elt))


def is_tagged_healthy(recipe):
    print(recipe['additional_info'])
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
            recipes_list.append(line[9:].replace("\n", ""))
    return recipes_list

def get_ids_recipes_CF_coverage_set():
    CF_recipes_list = list()
    with open(CF_reco_coverage_file_path, 'r') as CF_reco_f:
        for line in CF_reco_f:
            CF_recipes_list.append(line[9:-1].replace("\n", ""))
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


def get_mean(l):
    try:
        return stats.mean(l)
    except stats.StatisticsError:
        return "NA"

def get_std(l):
    try:
        return stats.stdev(l)
    except stats.StatisticsError:
        return "NA"


def get_int(string1):
    try:
        return int(re.search(r'\d+', string1).group())
    except AttributeError:
        return 0


def remove_prepcookservings(str1):
    str1 = str1.replace("Prep:", "")
    str1 = str1.replace("Cook:", "")
    str1 = str1.replace("Total:", "")
    if "-" in str1 and "Serves" not in str1:
        str1 = str1.split("-")[1]
    str1 = str1.replace("Serves", "")
    str1 = str1.replace(",", "")
    str1 = str1.strip()
    return str1

def convert_timestring_to_intminutes(timestring):
    if timestring == '0S':
        return -1
    if 'H' in timestring:
        timestring = timestring.replace('H', " H ")
    if 'M' in timestring:
        timestring = timestring.replace('M', " M ")
    timestring.strip()
    splited = timestring.split()
    int_list = list()
    for elt in splited:
        if elt == 'min' or elt == 'mins' or elt == 'M':
            int_list.append(1)
        elif elt == 'hr' or elt == 'hrs' or elt == 'H':
            int_list.append(60)
        else:
            int_list.append(get_int(elt))
    if not (len(int_list) == 2 or len(int_list) == 4):
        raise ValueError("Cannot convert %s to minutes!" % timestring)
    else:
        t = int_list[0] * int_list[1]
        if len(int_list) == 4:
            t += (int_list[2] * int_list[3])
    return t


def convert_timeInt_to_timeStr(timeInt):
    if timeInt == 0:
        return None
    h = timeInt // 60
    m = timeInt % 60
    h_str = ""
    if h == 1:
        h_str = h.__str__() + " hr"
    elif h > 1:
        h_str = h.__str__() + "hrs"
    m_str = ""
    if m == 1:
        m_str = m.__str__() + "min"
    elif m > 1:
        m_str = m.__str__() + "mins"
    total_str = h_str
    if total_str != "":
        total_str += ", "
    total_str += m_str
    return total_str
