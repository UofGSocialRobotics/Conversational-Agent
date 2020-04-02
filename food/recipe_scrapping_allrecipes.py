from bs4 import BeautifulSoup
import requests
import json
import re
from selenium import webdriver
import food.food_dataparser as food_dataparser

PASTA = False
DISHES = False
FISH = True
MEAT = False
EGGS = False
VEG = False
FRUITS = False

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.7) Gecko/2009021910 Firefox/3.0.7'
}

INGREDIENTS_CATEGORIES_TO_SCRAP = ['vegetables', 'fruits', 'pulses', 'gourds', 'meat', 'fish', 'eggs', 'dishes', 'pasta', 'cereals']

RECIPES_TO_SCRAP = "food/resources/recipes_DB/recipes_to_scrap_allrecipes.json"

if PASTA:
    INGREDIENTS_CATEGORIES_TO_SCRAP = ['pasta']
    RECIPES_TO_SCRAP = "food/resources/recipes_DB/recipes_to_scrap_allrecipes_pasta.json"
if DISHES:
    INGREDIENTS_CATEGORIES_TO_SCRAP = ['dishes']
    RECIPES_TO_SCRAP = "food/resources/recipes_DB/recipes_to_scrap_allrecipes_dishes.json"
if FISH:
    INGREDIENTS_CATEGORIES_TO_SCRAP = ['fish']
    RECIPES_TO_SCRAP = "food/resources/recipes_DB/recipes_to_scrap_allrecipes_fish.json"
if MEAT:
    INGREDIENTS_CATEGORIES_TO_SCRAP = ['meat']
    RECIPES_TO_SCRAP = "food/resources/recipes_DB/recipes_to_scrap_allrecipes_meat.json"
if EGGS:
    INGREDIENTS_CATEGORIES_TO_SCRAP = ['eggs']
    RECIPES_TO_SCRAP = "food/resources/recipes_DB/recipes_to_scrap_allrecipes_eggs.json"
if VEG:
    INGREDIENTS_CATEGORIES_TO_SCRAP = ['vegetables']
    RECIPES_TO_SCRAP = "food/resources/recipes_DB/recipes_to_scrap_allrecipes.json"
if FRUITS:
    INGREDIENTS_CATEGORIES_TO_SCRAP = ['fruits']
    RECIPES_TO_SCRAP = "food/resources/recipes_DB/recipes_to_scrap_allrecipes_fruits.json"

with open(RECIPES_TO_SCRAP, 'r') as f:
    content = json.load(f)
scrapped_ingredients = content['json_scrapped_ingredients']
recipes_to_scrap = content['recipes_to_scrap']
recipe_to_seed_ingredient_dict = content['recipe_to_seed_ingredient_dict']


def get_int(string1):
    return int(re.search(r'\d+', string1).group())


def convert_timestring_to_intminutes(timestring):
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

def scrap_recipe(recipe_id='14597/slovak-stuffed-cabbage/'):
    query = "https://www.allrecipes.com/recipe/" + recipe_id
    soup = BeautifulSoup(requests.get(query, headers=HEADERS).content, "html.parser")
    # title = scrap_title(soup)
    # ratings_info = scrap_ratings_info(soup)
    # img_url = scrap_image(soup)
    # recipe_info = scrap_recipe_info(soup)
    # ingredients_list = scrap_ingredients_list(soup)
    # instructions = scrap_instructions(soup)
    nutrition_info = scrap_nutrition_info(soup)


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
    print(recipe_info)


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


def scrap_nutrition_info(soup):
    script = soup.find('script', {'type': 'application/ld+json'})
    json_script = json.loads(script.text)
    recipe_info = json_script[1]
    title = recipe_info['name']
    print(title)
    recipe_url = recipe_info['mainEntityOfPage']
    print(recipe_url)
    img_url = recipe_info['image']['url']
    print(img_url)
    description = recipe_info['description']
    print(description)
    prep_time_str = recipe_info['prepTime'][2:]
    prep_time_int = convert_timestring_to_intminutes(prep_time_str)
    print(prep_time_str, prep_time_int)
    cook_time_str = recipe_info['cookTime'][2:]
    cook_time_int = convert_timestring_to_intminutes(cook_time_str)
    print(cook_time_str, cook_time_int)
    total_time_str = recipe_info['totalTime'][2:]
    total_time_int = convert_timestring_to_intminutes(total_time_str)
    print(total_time_str, total_time_int)
    ingredients = recipe_info['recipeIngredient']
    print(ingredients)
    instructions = [step['text'] for step in recipe_info['recipeInstructions']]
    print(instructions)
    recipe_category = recipe_info['recipeCategory']
    print(recipe_category)
    rating_avg = recipe_info['aggregateRating']['ratingValue']
    print(rating_avg)
    nutrition_info = recipe_info['nutrition']
    print(nutrition_info)

    # with open('food/resources/recipes_DB/json_script.json', 'w') as f:
    #     json.dump(json_script, f, indent=True)


def scrap_comments(recipe='222509/easy-and-quick-halushki/', page=9):
    url = 'https://www.allrecipes.com/recipe/' + recipe + '?page=' + page.__str__()
    browser = webdriver.Firefox()
    browser.get(url)
    html = browser.page_source
    print(url)
    # soup = BeautifulSoup(requests.get(url, headers=HEADERS).content, "html.parser")
    soup = BeautifulSoup(html, features="html.parser")
    res_list = soup.findAll('div', {'class': 'recipe-review-body'})
    for res in res_list:
        print(res.text.strip())
    print(len(res_list))
    browser.quit()

def get_number_of_ingredients_before(ingredient):
    ingredients_list = get_seed_ingredients()
    print(ingredients_list.index(ingredient))


def get_seed_ingredients():
    seed_ingredients = list()
    for category, foods in food_dataparser.extensive_food_DBs.category_to_foods.items():
        if category in INGREDIENTS_CATEGORIES_TO_SCRAP:
            seed_ingredients += foods
    print("ingredients to scrap = ", len(seed_ingredients))
    return seed_ingredients


def save_recipes_to_scrap():
    with open(RECIPES_TO_SCRAP, 'w') as fjson:
        data = dict()
        data['json_scrapped_ingredients'] = scrapped_ingredients
        data['recipes_to_scrap'] = recipes_to_scrap
        data['recipe_to_seed_ingredient_dict'] = recipe_to_seed_ingredient_dict
        json.dump(data, fjson, indent=True)


def get_all_recipes_with_access_to_comments(food='lasagna', idx_page=1):
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
            idx_page += 1
            print("Page %d, so far %d recipes we could scrap" % (idx_page, len(recipes_ids_list)))
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
                get_all_recipes_with_access_to_comments(ingredient, 1)
            else:
                if ingredient != food:
                    print("Pass ingredient ", ingredient)
                else:
                    print("\n%d ingredients done (%.2f%%)\n" % (i-1, 100*float(i-1)/len(ingredients_list)))
                    get_all_recipes_with_access_to_comments(ingredient, idx)
                    stop_passing = True
        else:
            get_all_recipes_with_access_to_comments(ingredient, 1)
            stop_passing = True


if __name__ == "__main__":
    # find_recipes_on_page()
    # check_access_to_comments()

    # get_all_recipes_with_access_to_comments()

    ## --- Scrap recipes
    seed_ingredients = get_seed_ingredients()
    print(seed_ingredients)
    get_all_ids_recipes_to_scrap(seed_ingredients)


    # get_number_of_ingredients_before("cherry tomato")
    # scrap_recipe()
    # scrap_comments()
