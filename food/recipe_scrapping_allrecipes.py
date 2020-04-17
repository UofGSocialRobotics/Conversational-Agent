from bs4 import BeautifulSoup
import requests
import json
import re
import time
import random
from selenium import webdriver
import food.food_dataparser as food_dataparser



HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.7) Gecko/2009021910 Firefox/3.0.7'
}


#########################################################################################################
##                                            COLLECT RECIPE IDs                                       ##
#########################################################################################################


## ------------------------------------------      Set up        ------------------------------------  ##

PASTA = False
DISHES = False
FISH = False
MEAT = False
EGGS = False
VEG = False
FRUITS = False
PULSES = False
GOURDS =False
CEREALS = False
FRUITS_REVERSE = False


###################################

FRUITS_REVERSE = True

###################################

INGREDIENTS_CATEGORIES_TO_SCRAP = ['vegetables', 'fruits', 'pulses', 'gourds', 'meat', 'fish', 'eggs', 'dishes', 'pasta', 'cereals']

RECIPES_TO_SCRAP = "food/resources/recipes_DB/allrecipes/recipes_to_scrap_allrecipes.json"

if PASTA:
    INGREDIENTS_CATEGORIES_TO_SCRAP = ['pasta']
    RECIPES_TO_SCRAP = "food/resources/recipes_DB/allrecipes/recipes_to_scrap_allrecipes_pasta.json"
elif DISHES:
    INGREDIENTS_CATEGORIES_TO_SCRAP = ['dishes']
    RECIPES_TO_SCRAP = "food/resources/recipes_DB/allrecipes/recipes_to_scrap_allrecipes_dishes.json"
elif FISH:
    INGREDIENTS_CATEGORIES_TO_SCRAP = ['fish']
    RECIPES_TO_SCRAP = "food/resources/recipes_DB/allrecipes/recipes_to_scrap_allrecipes_fish.json"
elif MEAT:
    INGREDIENTS_CATEGORIES_TO_SCRAP = ['meat']
    RECIPES_TO_SCRAP = "food/resources/recipes_DB/allrecipes/recipes_to_scrap_allrecipes_meat.json"
elif EGGS:
    INGREDIENTS_CATEGORIES_TO_SCRAP = ['eggs']
    RECIPES_TO_SCRAP = "food/resources/recipes_DB/allrecipes/recipes_to_scrap_allrecipes_eggs.json"
elif VEG:
    INGREDIENTS_CATEGORIES_TO_SCRAP = ['vegetables']
    RECIPES_TO_SCRAP = "food/resources/recipes_DB/allrecipes/recipes_to_scrap_allrecipes.json"
elif FRUITS:
    INGREDIENTS_CATEGORIES_TO_SCRAP = ['fruits']
    RECIPES_TO_SCRAP = "food/resources/recipes_DB/allrecipes/recipes_to_scrap_allrecipes_fruits.json"
elif PULSES:
    INGREDIENTS_CATEGORIES_TO_SCRAP = ['pulses']
    RECIPES_TO_SCRAP = "food/resources/recipes_DB/allrecipes/recipes_to_scrap_allrecipes_pulses.json"
elif GOURDS:
    INGREDIENTS_CATEGORIES_TO_SCRAP = ['gourds']
    RECIPES_TO_SCRAP = "food/resources/recipes_DB/allrecipes/recipes_to_scrap_allrecipes_gourds.json"
elif CEREALS:
    INGREDIENTS_CATEGORIES_TO_SCRAP = ['cereals']
    RECIPES_TO_SCRAP = "food/resources/recipes_DB/allrecipes/recipes_to_scrap_allrecipes_cereals.json"
elif FRUITS_REVERSE:
    INGREDIENTS_CATEGORIES_TO_SCRAP = ['fruits']
    RECIPES_TO_SCRAP = "food/resources/recipes_DB/allrecipes/recipes_to_scrap_allrecipes_fruits_reverse.json"

with open(RECIPES_TO_SCRAP, 'r') as f:
    content = json.load(f)
scrapped_ingredients = content['json_scrapped_ingredients']
recipes_to_scrap = content['recipes_to_scrap']
recipe_to_seed_ingredient_dict = content['recipe_to_seed_ingredient_dict']



## ------------------------------------------ ID collection functions ------------------------------------  ##



def get_number_of_ingredients_before(ingredient):
    ingredients_list = get_seed_ingredients()
    print(ingredients_list.index(ingredient))


def get_seed_ingredients():
    seed_ingredients = list()
    for category, foods in food_dataparser.extensive_food_DBs.category_to_foods.items():
        if category in INGREDIENTS_CATEGORIES_TO_SCRAP:
            seed_ingredients += foods
    new_list = list()
    for i in seed_ingredients:
        if not ("bread" in i or "tortilla" in i):
            new_list.append(i)
    seed_ingredients = new_list
    print("ingredients to scrap = ", len(seed_ingredients))
    return seed_ingredients


def save_recipes_to_scrap():
    with open(RECIPES_TO_SCRAP, 'w') as fjson:
        data = dict()
        data['json_scrapped_ingredients'] = scrapped_ingredients
        data['recipes_to_scrap'] = recipes_to_scrap
        data['recipe_to_seed_ingredient_dict'] = recipe_to_seed_ingredient_dict
        json.dump(data, fjson, indent=True)


def get_allrecipes_with_access_to_comments(food='lasagna', idx_page=1):
    print("\n------ Seed ingredient = ", food)
    # idx_page = 1
    scrapped_ingredients.append([food, 0])
    recipes_ids_list = list()
    while (idx_page):
        query = "https://www.allrecipes.com/search/results/?wt=" + food + "&page=" + idx_page.__str__()
        res_list = find_recipes_on_page(query)
        for res in res_list:
            if check_access_to_comments(res):
                if res not in recipe_to_seed_ingredient_dict.keys():
                    recipe_to_seed_ingredient_dict[res] = list()
                recipe_to_seed_ingredient_dict[res].append(food)
                if res not in recipes_to_scrap:
                    recipes_to_scrap.append(res)
                    recipes_ids_list.append(res)
        del scrapped_ingredients[:-1]
        scrapped_ingredients.append([food, idx_page])
        if idx_page % 5 == 0 or idx_page == 1:
            save_recipes_to_scrap()
        if res_list:
            print("Page %d, so far %d recipes we could scrap" % (idx_page, len(recipes_ids_list)))
            idx_page += 1
        else:
            idx_page = 0
            save_recipes_to_scrap()
    print("----- >> Got %d recipes with comment access for food %s" % (len(recipes_ids_list), food))


def find_recipes_on_page(query="https://www.allrecipes.com/search/results/?wt=lasagna&page=15"):
    if ' ' in query:
        query = query.replace(' ', '%20')
    # print(query)
    recipes_list = list()
    soup = BeautifulSoup(requests.get(query, headers=HEADERS).content, "html.parser")
    articles_list = soup.findAll('article')
    for a in articles_list:
        # print(a)
        recipe_title = a.find('span', {'class': 'fixed-recipe-card__title-link'})
        # print(recipe_title)
        if recipe_title:
            reviews_c = a.find('format-large-number')
            if reviews_c:
                reviews_c = int(reviews_c['number'])
                if reviews_c > 9:
                    # print(reviews_c)
                    recipe_link = a.find('a', {'class': 'fixed-recipe-card__title-link'})
                    recipe_id = recipe_link['href'].split("recipe/")[1]
                    recipes_list.append(recipe_id)
    # print(recipes_list)
    return recipes_list


def check_access_to_comments(recipe_id="19344/homemade-lasagna"):
    query = "https://www.allrecipes.com/recipe/" + recipe_id + "?page=2" # works
    # query = "https://www.allrecipes.com/recipe/220094/eggplant-lasagna/?page=2" # does not work
    soup = BeautifulSoup(requests.get(query, headers=HEADERS).content, "html.parser")
    back_link = soup.find('span', {'class': 'recipe-review-back-text'})
    return back_link != None


def get_all_ids_recipes_to_scrap(ingredients_list=['lasagna']):

    stop_passing = False
    for i, ingredient in enumerate(ingredients_list):
        if scrapped_ingredients:
            food, idx = scrapped_ingredients[0][0], scrapped_ingredients[0][1]
            if stop_passing:
                get_allrecipes_with_access_to_comments(ingredient, 1)
            else:
                if ingredient != food:
                    print("Pass ingredient ", ingredient)
                else:
                    print("\n%d ingredients done (%.2f%%)\n" % (i-1, 100*float(i-1)/len(ingredients_list)))
                    get_allrecipes_with_access_to_comments(ingredient, idx)
                    stop_passing = True
        else:
            get_allrecipes_with_access_to_comments(ingredient, 1)
            stop_passing = True


def compile_recipe_id_lists_all_together():
    ingredients_categories = ['', 'fruits', 'pulses', 'gourds', 'meat', 'fish', 'eggs', 'dishes', 'pasta', 'fruits_reverse', 'cereals']
    file_path_root = "food/resources/recipes_DB/allrecipes/recipes_to_scrap_allrecipes"
    allrecipes_list = list()
    for cat in ingredients_categories:
        cat_str = "_" + cat if cat else ""
        file_path = file_path_root + cat_str + ".json"
        with open(file_path, 'r') as fjson:
            content = json.load(fjson)
            for r_id in content['recipes_to_scrap']:
                if r_id not in allrecipes_list:
                    allrecipes_list.append(r_id)
    print(len(allrecipes_list))
    with open(file_path_root + "_all.json", 'w') as fall:
        json.dump(allrecipes_list, fall, indent=True)
    return allrecipes_list



#########################################################################################################
##                                            SCRAP RECIPES                                            ##
#########################################################################################################


## ------------------------------------------      Set up        ------------------------------------  ##


FILE_PATH = "food/resources/recipes_DB/allrecipes/recipes_to_scrap_allrecipes_all.json"
RECIPES_USERS_DB_ROOT_PATH = "food/resources/recipes_DB/allrecipes/recipes_users_DB"
with open(FILE_PATH, 'r') as f:
    ALL_IDS_TO_SCRAP = json.load(f)

N_COLLECT = 10000

###################################

COLLECT_FROM = False
x_RATINGS_MIN = 100

###################################

# if isinstance(COLLECT_FROM, int) and COLLECT_FROM >=0:
#     ALL_IDS_TO_SCRAP = ALL_IDS_TO_SCRAP[COLLECT_FROM:COLLECT_FROM+N_COLLECT]
#     RECIPES_USERS_DB_ROOT_PATH += "_from_" + COLLECT_FROM.__str__()

RECIPES_USERS_DB_PATH = RECIPES_USERS_DB_ROOT_PATH + '.json'

ALL_DATA = dict()
with open(RECIPES_USERS_DB_PATH, 'r') as jsonf:
    ALL_DATA = json.load(jsonf)


## -----------------------------------------  Scrapping functions -----------------------------------  ##


def scrap_title(soup):
    title = soup.find('div', {'class': 'headline-wrapper'}).text.strip()
    return title


def scrap_ratings_info(soup):
    ratings_info = dict()
    soup_rc = BeautifulSoup(str(soup.find('div', {'class': 'recipe-ratings-list'})), features="html.parser")
    ratings_info['ratings_total'] = soup_rc.find('span', {'class': 'ratings-count'}).text.strip()
    rc_all = soup_rc.findAll('span', {'class': 'rating-count'})
    for i, rc_html in enumerate(rc_all):
        rc = rc_html.text.strip()
        ratings_info[i] = rc

    reviews_soup = BeautifulSoup(str(soup.find('ul', {'class': 'ugc-ratings-list'})), features="html.parser")
    reviews_c = get_int(reviews_soup.find('a').text.strip())
    ratings_info['reviews_total'] = reviews_c

    return ratings_info


def scrap_image(soup):
    soup_img = BeautifulSoup(str(soup.find('div', {'class': 'image-container'})), features="html.parser")
    img_url = soup_img.find('img')['src']
    return img_url


def scrap_recipe_info(soup):
    recipe_info = dict()
    soup_img = BeautifulSoup(str(soup.find('aside', {'class': 'recipe-info-section'})), features="html.parser")
    res_list = soup_img.findAll('div', {'class': 'recipe-meta-item-body'})
    prep = res_list[0].text.strip()
    recipe_info['prep_text'] = prep
    recipe_info['prep_int'] = convert_timestring_to_intminutes(prep)
    cook = res_list[1].text.strip()
    recipe_info['cook_text'] = cook
    recipe_info['cook_int'] = convert_timestring_to_intminutes(cook)
    total = res_list[2].text.strip()
    recipe_info['total_text'] = total
    recipe_info['total_int'] = convert_timestring_to_intminutes(total)
    recipe_info['servings'] = get_int(res_list[3].text.strip())
    # print(recipe_info)


def scrap_ingredients_list(soup):
    i_list = list()
    res_list = soup.findAll('span', {'class': 'ingredients-item-name'})
    for res in res_list:
        i_list.append(res.text.strip())
    return i_list


def scrap_instructions(soup):
    instructions = list()
    soup_instructions = BeautifulSoup(str(soup.find('ul', {'class': 'instructions-section'})), features="html.parser")
    res_list = soup_instructions.findAll('div', {'class': 'section-body'})
    for res in res_list:
        instructions.append(res.text.strip())
    return instructions


def scrap_recipe_data(soup):
    recipe_data = dict()
    script = soup.find('script', {'type': 'application/ld+json'})
    json_script = json.loads(script.text)
    recipe_info = json_script[1]
    title = recipe_info['name']
    recipe_data['title'] = title
    recipe_url = recipe_info['mainEntityOfPage']
    recipe_data['url'] = recipe_url
    img_url = recipe_info['image']['url']
    recipe_data['img_url'] = img_url
    description = recipe_info['description']
    recipe_data['desciption'] = description
    prep_time_str = recipe_info['prepTime'][2:]
    prep_time_int = convert_timestring_to_intminutes(prep_time_str)
    recipe_data['prep_time_str'] = prep_time_str
    recipe_data['prep_time_int'] = prep_time_int
    cook_time_str = recipe_info['cookTime'][2:]
    cook_time_int = convert_timestring_to_intminutes(cook_time_str)
    recipe_data['cook_time_str'], recipe_data['cook_time_int'] = cook_time_str, cook_time_int
    total_time_str = recipe_info['totalTime'][2:]
    total_time_int = convert_timestring_to_intminutes(total_time_str)
    recipe_data['total_time_str'], recipe_data['total_time_int'] = total_time_str, total_time_int
    ingredients = recipe_info['recipeIngredient']
    recipe_data['ingredients'] = ingredients
    instructions = [step['text'] for step in recipe_info['recipeInstructions']]
    recipe_data['instructions'] = instructions
    recipe_category = recipe_info['recipeCategory']
    recipe_data['category'] = recipe_category
    # rating_avg = recipe_info['aggregateRating']['ratingValue']
    # print(rating_avg)
    nutrition_info = recipe_info['nutrition']
    recipe_data['nutrition_info'] = nutrition_info

    return recipe_data


def scrap_all_comments(recipe='220875/deconstructed-chicken-kiev/', n_reviews=99):
    n_page_max = n_reviews / 9 + 1
    page = 2
    all_ratings = list()
    while page <= n_page_max:
        new_comments = scrap_comments_on_page(recipe, page)
        if new_comments:
            users_who_already_commented = [d['user_id'] for d in all_ratings]
            for comment in new_comments:
                user = comment['user_id']
                if user not in users_who_already_commented:
                    all_ratings.append(comment)
            page += 1
        else:
            break
    print(recipe, len(all_ratings))
    return all_ratings



def scrap_comments_on_page(recipe='222509/easy-and-quick-halushki/', page=90):
    ratings_data_list = list()
    url = 'https://www.allrecipes.com/recipe/' + recipe + '?page=' + page.__str__()
    browser = webdriver.Safari()
    browser.get(url)
    html = browser.page_source
    # print(url)
    # soup = BeautifulSoup(requests.get(url, headers=HEADERS).content, "html.parser")
    soup = BeautifulSoup(html, features="html.parser")
    res_list = soup.findAll('div', {'class': 'component ugc-review ugc-item recipe-review-wrapper'})
    for res in res_list:
        review = dict()
        res_soup = BeautifulSoup(str(res), features="html.parser")
        try:
            user_id = res_soup.find('a', {"class": 'recipe-review-author'})['href'].split(".com/")[1]
            review['user_id'] = user_id
            user_name = res_soup.find('span', {"class": 'reviewer-name'}).text.strip()
            review['user_name'] = user_name
            rating = res_soup.find('span', {"class": 'review-star-text'}).text.strip()
            rating = get_int(rating)
            review['rating'] = rating
            comment = res_soup.find('div', {"class": 'recipe-review-body'}).text.strip()
            review['comment'] = comment
            ratings_data_list.append(review)
        except TypeError:
            print("TypeError on", url)
    # for res in res_list:
    #     print(res.text.strip())
    # print(page, len(ratings_data_list))
    browser.quit()
    return ratings_data_list


def scrap_recipe(recipe_id='14597/slovak-stuffed-cabbage/'):
    start = time.time()
    query = "https://www.allrecipes.com/recipe/" + recipe_id
    soup = BeautifulSoup(requests.get(query, headers=HEADERS).content, "html.parser")

    ratings_info = scrap_ratings_info(soup)
    nr = ratings_info['reviews_total']

    if nr >= x_RATINGS_MIN:

        recipe_data = scrap_recipe_data(soup)
        recipe_data['ratings_info'] = ratings_info
        all_comments = scrap_all_comments(recipe_id, n_reviews=nr)
        ncr = len(all_comments)
        recipe_data['all_ratings'] = all_comments

        total_time = time.time() - start
        total_min, total_s = total_time/60, total_time % 60

        print("For %s, %d comments, collected %d (%.2f%%) -- %dm%ds" % (recipe_id, nr, ncr, float(ncr)/nr*100, total_min, total_s))
        return recipe_data

    else:
        print("Pass %s, n ratings = %d" % (recipe_id, nr))
    # print(recipe_data)


def scrap_allrecipes_from_list(ids_list=['14597/slovak-stuffed-cabbage/']):
    for i, rid in enumerate(ids_list):
        print(i, rid)
        rdata = scrap_recipe(recipe_id=rid)
        if rdata:
            ALL_DATA[rid] = rdata
            with open(RECIPES_USERS_DB_PATH, 'w') as fw:
                json.dump(ALL_DATA, fw, indent=True)




if __name__ == "__main__":
    # find_recipes_on_page()
    # check_access_to_comments()

    # get_allrecipes_with_access_to_comments()

    ## --- Scrap recipes IDs for collection later
    # seed_ingredients = get_seed_ingredients()
    # if FRUITS_REVERSE:
    #     seed_ingredients = list(reversed(seed_ingredients))
    # print(seed_ingredients)
    # get_all_ids_recipes_to_scrap(seed_ingredients)

    ## --- Join json files
    all_ids = compile_recipe_id_lists_all_together()


    ## --- Test recipe scrapping

    # random_recipe_id = random.choice(all_ids)
    # print(random_recipe_id)

    # get_number_of_ingredients_before("cherry tomato")
    # scrap_recipe()
    # scrap_comments_on_page()


    ## --- Scrap recipes' data
    scrap_allrecipes_from_list(ALL_IDS_TO_SCRAP)

