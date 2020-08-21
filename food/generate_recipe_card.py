import json
import os
import random
import math
import urllib.request

from termcolor import colored

import food.resources.recipes_DB.allrecipes.nodejs_scrapper.consts as consts
from food.resources.img.recipe_card.html_large_recipe_card import *
from food.resources.img.recipe_card.html_small_recipe_card import *

img_dir_path = 'food/resources/recipes_DB/allrecipes/images/'



def ingredients_in_column(ingredients_list):
    n_ingredients = len(ingredients_list)
    n_ingredients_by_col, remainder = n_ingredients // 3, n_ingredients % 3
    extra_in_col_1 = 0 if remainder == 0 else 1
    extra_in_col_2 = 1 if remainder == 2 else 0
    limit_col1 = n_ingredients_by_col+extra_in_col_1
    limit_col2 = n_ingredients_by_col*2+extra_in_col_1+extra_in_col_2
    if limit_col1 == 1:
        col1 = [ingredients_list[0]]
    else:
        col1 = ingredients_list[:limit_col1]
    if (limit_col2 - limit_col1) == 1:
        col2 = [ingredients_list[limit_col1]]
    elif (limit_col2 - limit_col1) == 0:
        col2 = []
    else:
        col2 = ingredients_list[limit_col1:limit_col2]
    if n_ingredients - limit_col2 == 1:
        col3 = [ingredients_list[limit_col2]]
    elif n_ingredients - limit_col2 == 0:
        col3 = []
    else:
        col3 = ingredients_list[limit_col2:]
    return col1, col2, col3


def replace_fractions(line):
    line = line.replace("¾", "&frac34;")
    line = line.replace("½", "&frac12;")
    line = line.replace("¼", "&frac14;")
    line = line.replace("⅓", "&frac13;")
    line = line.replace("⅔", "&frac23;")
    line = line.replace("⅛", "&frac18;")
    line = line.replace("⅜", "&frac38;")
    line = line.replace("⅕", "&frac15;")
    line = line.replace("⅖", "&frac25;")
    line = line.replace("⅗", "&frac35;")
    line = line.replace("⅝", "&frac58;")
    line = line.replace(" ", " ")
    line = line.replace("™", "&trade;")
    line = line.replace("®", "&reg;")
    line = line.replace("©", "&copy")
    line = line.replace("℃", "&#8451;")
    line = line.replace("℉", "&#8457;")
    return line


def generate_card(rid, rdata, size="large"):

    fname = "food/resources/img/recipe_img/"+rid+".jpg"
    if not os.path.isfile(fname):
        urllib.request.urlretrieve(rdata["image_url"], fname)

    prep_time = "--"
    if "Prep" in rdata["time_info"].keys():
        prep_time = rdata["time_info"]["Prep"]
    cook_time = "--"
    if "Cook" in rdata["time_info"].keys():
        cook_time = rdata["time_info"]["Cook"]
    total_time = "--"
    if "Total" in rdata["time_info"].keys():
        total_time = rdata["time_info"]["Total"]
    servings = "--"
    if "Servings" in rdata["time_info"].keys():
        servings = rdata["time_info"]["Servings"]

    fsa_score = rdata['FSAscore']
    if fsa_score < 7:
        color = "green"
    elif fsa_score > 9:
        color = "red"
    else:
        color = "orange"

    rating = rdata["rating"]
    n_stars_int = math.floor(rating)
    reminder = rating - n_stars_int
    half_star = False
    if 0.25 <= reminder < 0.75:
        half_star = True
    elif reminder >= 0.75:
        n_stars_int += 1

    n_stars_pic = "stars" + n_stars_int.__str__()
    if half_star:
        n_stars_pic += ".5"
    n_stars_pic += ".png"

    if size=="large":

        col1, col2, col3 = ingredients_in_column(rdata['ingredients'])
        col1 = "<span>" + "</span><br><br><span>".join(col1) + "</span>"
        col1 = replace_fractions(col1)
        col2 = "<span>" + "</span><br><br><span>".join(col2) + "</span>"
        col2 = replace_fractions(col2)
        col3 = "<span>" + "</span><br><br><span>".join(col3) + "</span>"
        col3 = replace_fractions(col3)

        instructions = "<ol><li>" + "</li><br><li>".join(rdata['instructions']) + "</li></ol>"

        description = rdata['description'] if 'description' in rdata.keys() else ""
        if not description:
            print(colored("WARNING: no description for %s" % rid, "red"))

        html_page = large_card_html1 + rid+".jpg" \
                    + large_card_html2 + rdata["title"] \
                    + large_card_html3 + n_stars_pic \
                    + large_card_html4 + "("+rdata['n_reviews_collected'].__str__()+")" \
                    + large_card_html4_bis + "healthiness_" + color+".png" \
                    + large_card_html5 + prep_time \
                    + large_card_html6 + cook_time \
                    + large_card_html7 + total_time \
                    + large_card_html8 + servings \
                    + large_card_html8_bis + description \
                    + large_card_html8_ter + col1 \
                    + large_card_html9 + col2 \
                    + large_card_html10 + col3 \
                    + large_card_html11 + instructions \
                    + large_card_html12

    elif size == "small":

        ingredients = replace_fractions(", ".join(rdata['ingredients']))
        # if len(ingredients) > 95:
        #     new_ingredients = ingredients[:95]
        #     if ingredients[95] != " ":
        #         new_ingredients_list = new_ingredients.split()[:-1]
        #         new_ingredients = " ".join(new_ingredients_list)

        title = rdata["title"]
        if len(title) > 30:
            title = title[:27] + "..."

        html_page = small_card_html1 + rid+".jpg" \
                    + small_card_html2 + title \
                    + small_card_html3 + n_stars_pic \
                    + small_card_html4 + "("+rdata['n_reviews_collected'].__str__()+")" \
                    + small_card_html4_bis + "healthiness_" + color+".png" \
                    + small_card_html5 + prep_time \
                    + small_card_html6 + cook_time \
                    + small_card_html7 + total_time \
                    + small_card_html8 + ingredients \
                    + small_card_html9

    else:
        print("Invalid size!")

    f = open("food/resources/img/recipe_card/"+size+"/HTMLs/"+rid+".html", "w")
    f.write(html_page)
    f.close()


def generate_all_recipe_cards(size="large"):

    # for i in range(10):
    with open(consts.json_xUsers_Xrecipes_path, 'r') as fjson:
        content = json.load(fjson)
        for rid, rdata in content['recipes_data'].items():
            print(rid)
            rid_noSlash = rid.replace("/", "")
            try:
                generate_card(rid_noSlash, rdata, size)
            except KeyError:
                print(colored("Error with %s" % rid, 'red'))


def test_generate_random_card(size="large"):
    with open(consts.json_xUsers_Xrecipes_path, 'r') as fjson:
        content = json.load(fjson)
        random_id = random.choice(list(content['recipes_data'].keys()))
        random_data = content['recipes_data'][random_id]
        rid_noSlash = random_id.replace("/", "")
        generate_card(rid_noSlash, random_data, size)


def rename_recipe_cards():

    mypath = 'food/resources/img/'

    onlyfiles = [f for f in os.listdir(mypath) if os.path.isfile(mypath + f)]
    for f in onlyfiles:
        if "-full.png" in f:
            # print(f)
            new_name = f.replace("fileUserslucilecaDesktopConversational_Agentserver_sidefoodresourcesimgrecipe_card", "")
            new_name = new_name.replace("smallHTMLs", "")
            new_name = new_name.replace("-full", "")
            os.rename(mypath+f, mypath+new_name)


def move_PNGs_to_PNGs_folder():
    mypath = 'food/resources/img/'
    mynewpath = 'food/resources/img/recipe_card/small/PNGs/'
    onlyPNGfiles = [f for f in os.listdir(mypath) if (os.path.isfile(mypath + f) and ".png" in f)]
    for f in onlyPNGfiles:
        os.rename(mypath+f, mynewpath+f)


def move_HTMLs_to_HTMLs_folder():
    mypath = 'food/resources/img/recipe_card/'
    mynewpath = 'food/resources/img/recipe_card/HTMLs/'
    onlyPNGfiles = [f for f in os.listdir(mypath) if (os.path.isfile(mypath + f) and ".html" in f)]
    for f in onlyPNGfiles:
        os.rename(mypath+f, mynewpath+f)

if __name__ == "__main__":
    # move_HTMLs_to_HTMLs_folder()
    # test_generate_random_card("small")
    # generate_all_recipe_cards(size="small")
    # rename_recipe_cards()
    move_PNGs_to_PNGs_folder()
