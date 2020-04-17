from recipe_scrapers import scrape_me
import json
import food.food_dataparser as food_dataparser
import re
from bs4 import BeautifulSoup
import requests
import sys
import os
import food.RS_utils as rs_utils

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.7) Gecko/2009021910 Firefox/3.0.7'
}

INGREDIENTS_CATEGORIES_TO_SCRAP = ['vegetables', 'fruits', 'pulses', 'gourds', 'meat', 'fish', 'eggs', 'dishes', 'pasta', 'cereals']

file_path = 'food/resources/recipes_DB/BBCGoodFood/without0ratings/recipes_users_DB.json'

explored_ingredients = list()
recipes_to_ratings = dict()
ingredients_to_recipes = dict()
recipes_to_scrap_list = list()


if os.path.isfile(file_path):
    with open(file_path, 'r') as f_recipe_user_data:
        content = json.load(f_recipe_user_data)
        recipes_dict = content['recipes_data']
        users_names = content['users_list']
        users_comments_data = content['users_data']
else:
    recipes_dict = dict()
    users_names = list()
    users_comments_data = dict()


print("n users = %d" % len(users_names))
users_with_more_than_5_comments = 0
for user, data in users_comments_data.items():
    if data['n_comments'] >= 5:
        users_with_more_than_5_comments += 1
print("n users with > 5 comments = %d" % users_with_more_than_5_comments)

print("n recipes = %d" % len(recipes_dict))

to_scrap = [
    #test
    'https://www.bbcgoodfood.com/recipes/spinach-sweet-potato-lentil-dhal'
]

def get_seed_ingredients():
    seed_ingredients = list()
    for category, foods in food_dataparser.extensive_food_DBs.category_to_foods.items():
        if category in INGREDIENTS_CATEGORIES_TO_SCRAP:
            seed_ingredients += foods
    print("ingredients to scrap = ", len(seed_ingredients))
    return seed_ingredients

def find_recipes(ingredients_list=['farfal']):
    print("%d seed ingredients to look for" % len(ingredients_list))

    url = "https://www.bbcgoodfood.com/search/recipes?query="
    for ingredient in ingredients_list:
        n_recipes_seen = 0
        page_i = 0

        query = url + ingredient
        soup = BeautifulSoup(requests.get(query, headers=HEADERS).content, "html.parser")

        n_res = int(re.search(r'\d+', soup.find('h1', {'class': 'search-title'}).text).group())

        print("\nIngredient = %s, n results = %d to explore" % (ingredient, n_res))


        # scrap first page of results
        n_recipes_on_page = find_recipes_on_page(soup, ingredient)
        n_recipes_seen += n_recipes_on_page

        # scrap remaining pages if necessary
        while n_recipes_seen < n_res:
            page_i += 1
            sys.stdout.write("\rExploring page %d" % page_i)
            sys.stdout.flush()
            new_query = query + "&page=" + page_i.__str__()
            new_soup = BeautifulSoup(requests.get(new_query, headers=HEADERS).content, "html.parser")
            n_recipes_on_page = find_recipes_on_page(new_soup, ingredient)
            n_recipes_seen += n_recipes_on_page

        explored_ingredients.append(ingredient)

        #feedback to user
        if ingredient in ingredients_to_recipes.keys():
            print("\rFound %d recipes with 30 or more ratings for ingredient %s" % (len(ingredients_to_recipes[ingredient]), ingredient))
        else:
            print("\rFound no results with 30 or more ratings for ingredient %s" % ingredient)
        print("--> %d recipes with 30 or more ratings to scrap" % len(recipes_to_scrap_list))

        #save data
        json_recipes_to_scrap = dict()
        json_recipes_to_scrap['explored_ingredients'] = explored_ingredients
        json_recipes_to_scrap['recipes_list'] = recipes_to_scrap_list
        json_recipes_to_scrap['recipes_to_ratings'] = recipes_to_ratings
        json_recipes_to_scrap['ingredients_to_recipes'] = ingredients_to_recipes
        with open('food/resources/recipes_DB/recipes_to_scrap.json', 'w') as f:
            json.dump(json_recipes_to_scrap, f, indent=True)




def find_recipes_on_page(soup, ingredient):
    if ingredient not in ingredients_to_recipes.keys():
        ingredients_to_recipes[ingredient] = list()
    n_recipes_on_page = 0
    query_res_soup = BeautifulSoup(str(soup.find('div', {'id': 'search-results'})), features="html.parser")
    articles_list = query_res_soup.findAll('article')
    for article in articles_list:
        try:
            n_recipes_on_page += 1
            res_a = article.findAll('a')
            link = res_a[1]['href'] if len(res_a) == 2 else res_a[0]['href']
            res_p = article.findAll('p')
            n_ratings = int(re.search(r'\d+', res_p[0].text).group())
            if n_ratings >= 30 and link not in recipes_to_scrap_list:
                recipes_to_scrap_list.append(link)
                recipes_to_ratings[link] = n_ratings
            if n_ratings >= 30:
                ingredients_to_recipes[ingredient].append(link)
        except IndexError:
            pass

    return n_recipes_on_page

def scraping():

    with open('food/resources/recipes_DB/recipes_to_scrap.json', 'r') as fin:
        content = json.load(fin)
        recipes_passed = 0
        for i, recipe_id in enumerate(content['recipes_list']):
            if recipes_passed:
                print("%d recipes passed" % recipes_passed)
                recipes_passed = 0
            url = "https://www.bbcgoodfood.com/" + recipe_id
            if recipe_id not in recipes_dict.keys():
                try:
                    recipe = scrap_recipe_at(url, recipe_id, i)
                    recipes_dict[recipe_id] = recipe
                except ssl.SSLEOFError:
                    print("Error with recipe %s" % recipe_id)
            else:
                recipes_passed += 1
                # print("pass %s" % recipe_id)

            if i % 50 == 0:
                save_recipes_users_data()

    save_recipes_users_data()

def save_recipes_users_data():
    recipes_users_data = dict()
    recipes_users_data['recipes_data'] = recipes_dict
    recipes_users_data['users_list'] = users_names
    recipes_users_data['users_data'] = users_comments_data
    with open(file_path, 'w') as f:
        json.dump(recipes_users_data, f, indent=True)
        print("Save data in", file_path)


def scrap_recipe_at(url='https://www.bbcgoodfood.com/recipes/aubergine-goats-cheese-pasta', id=-1, i=-1):
        print("scrapping recipe %s (# %d)" % (id, i))
        recipe = dict()
        # give the url as a string, it can be url from any site listed below
        scraper = scrape_me(url)

        recipe['id'] = id
        recipe['title'] = scraper.title()
        recipe['total_time'] = scraper.total_time()
        # recipe['title'] = scraper.yields())
        ingredients = scraper.ingredients()
        recipe['ingredients'] = list()
        for ingredient in ingredients:
            if len(ingredient) % 2 == 0 and ingredient[:int(len(ingredient)/2)] == ingredient[int(len(ingredient)/2):]:
                recipe['ingredients'].append(ingredient[:int(len(ingredient)/2)])
            else:
                recipe['ingredients'].append(ingredient)
        recipe['instructions'] = scraper.instructions().split('\n')
        image_link = scraper.image()
        if not image_link:
            recipe['image_link'] = None
        else:
            recipe['image_link'] = 'https:' + image_link
        recipe['nutrition'] = scraper.nutrition()
        recipe['additional_info'] = scraper.additional_info()
        recipe['url'] = url
        recipe['ratings'] = scraper.rating_info()
        comments = scrap_comments(scraper, url)

        comments_wo_duplicates = list()
        already_seen_users = list()
        for comment in comments:
            user_name = comment['user_name']
            if user_name not in already_seen_users:
                already_seen_users.append(user_name)
                comments_wo_duplicates.append(comment)

        comments = comments_wo_duplicates

        recipe['comments'] = comments

        #collect comments data
        for comment in comments:
            user_name = comment['user_name']
            if user_name not in users_names:
                users_names.append(user_name)
                users_comments_data[user_name] = dict()
                users_comments_data[user_name]['n_comments'] = 1
                users_comments_data[user_name]['recipes_commented'] = list()
                users_comments_data[user_name]['recipes_commented'].append(recipe['id'])
            else:
                users_comments_data[user_name]['n_comments'] += 1
                users_comments_data[user_name]['recipes_commented'].append(recipe['id'])
                if users_comments_data[user_name]['n_comments'] == 5:
                    print("%s --> 5 comments!" % user_name)


        if id == -1:
            print(recipe)
        # scrap_price(url)

        return recipe


def scrap_comments(scraper, url):
    n_comments, comments = scraper.comments()
    next_page = 1
    while len(comments) < n_comments:
        sys.stdout.write("\rComments page %d" % next_page)
        sys.stdout.flush()
        new_url = url + "?page=" + str(next_page)
        scraper = scrape_me(new_url)
        _, new_comments = scraper.comments()
        if not new_comments:
            break
        comments += new_comments
        next_page += 1
    return comments

def scrap_missing_info(recipe_url="https://www.bbcgoodfood.com/recipes/rarebit-pork-chops"):
    soup = BeautifulSoup(requests.get(recipe_url, headers=HEADERS).content, "html.parser")
    # Prep time
    prep_time_soup = BeautifulSoup(str(soup.find('span', {"class": 'recipe-details__cooking-time-prep'})), features="html5lib")
    prep_time_html = prep_time_soup.find("span")
    if prep_time_html:
        prep_time_str = rs_utils.remove_prepcookservings(prep_time_html.text.strip())
        prep_time_int = rs_utils.convert_timestring_to_intminutes(prep_time_str)
    else:
        # print("No prep time")
        prep_time_str = None
        prep_time_int = 0
    # print(prep_time_str, prep_time_int)
    # Cook time
    new_soup = BeautifulSoup(str(soup.find('span', {"class": 'recipe-details__cooking-time-cook'})), features="html5lib")
    cook_time_html = new_soup.find("span")
    if cook_time_html:
        cook_time_str = rs_utils.remove_prepcookservings(cook_time_html.text.strip())
        cook_time_int = rs_utils.convert_timestring_to_intminutes(cook_time_str)
    else:
        # print("No cook time")
        cook_time_str = None
        cook_time_int = 0
    # print(cook_time_str, cook_time_int)
    total_time_int = prep_time_int + cook_time_int
    if total_time_int == 0:
        print(" ---------------- /!\\ no time info !!! /!\\ ----------------")
    total_time_str = rs_utils.convert_timeInt_to_timeStr(total_time_int)
    # Servings
    new_soup = BeautifulSoup(str(soup.find('section', {"class": 'recipe-details__item recipe-details__item--servings'})), features="html5lib")
    servings_str = rs_utils.remove_prepcookservings(new_soup.find("span").text.strip())
    if servings_str:
        servings_int = rs_utils.get_int(servings_str)
    else:
        servings_int = 0
    # print(servings_str, servings_int)
    # Description
    description_str = soup.find('div', {"class": 'recipe-header__description'}).text.strip()
    # print(elt_str)
    return prep_time_str, prep_time_int, cook_time_str, cook_time_int, total_time_int, total_time_str, servings_str, servings_int, description_str


def scrap_missing_info_for_recipes_DB():
    i = 0
    for rid, r in recipes_dict.items():
        if i >= 100:
            print(i, rid)
            rurl = r['url']
            rurl = rurl.replace("recipes//", "recipes/")
            r["prep_time_str"], r["prep_time_int"], r["cook_time_str"], r["cook_time_int"], r["total_time_int"], r["total_time_str"], r["servings_str"], r["servings_int"], r["description"] = scrap_missing_info(rurl)
            if ((i + 1) % 100) == 0:
                save_recipes_users_data()
        i += 1
    save_recipes_users_data()

def scrap_time_full(url):
    soup = BeautifulSoup(requests.get(url, headers=HEADERS).content, "html.parser")
    # Prep time
    time_html = soup.find('span', {"class": 'recipe-details__cooking-time-full'})
    if time_html:
        time_str = time_html.text.strip()
    else:
        time_str = "--"
    print(time_str)
    return time_str




def get_recipes_missing_total_time():
    n, i = 0, 0
    for rid, r in recipes_dict.items():
        try:
            i += 1
            if r['total_time_int'] == 0:
                print(rid)
                rurl = r['url']
                rurl = rurl.replace("recipes//", "recipes/")
                r["total_time_str"] = scrap_time_full(rurl)
                n += 1
        except KeyError:
            print("KeyError at %s (%d)" % (rid, i))
            return
    save_recipes_users_data()
    print("\n-----\nRecipes with no total time: %d (%.2f%%)\n\n" % (n, float(n)/len(list(recipes_dict.values()))))
    print(recipes_dict["/recipes/ultimate-vanilla-ice-cream"]["prep_time_str"])
    print(recipes_dict["/recipes/ultimate-vanilla-ice-cream"]["prep_time_int"])
    print(recipes_dict["/recipes/ultimate-vanilla-ice-cream"]["cook_time_str"])
    print(recipes_dict["/recipes/ultimate-vanilla-ice-cream"]["cook_time_int"])
    print(recipes_dict["/recipes/ultimate-vanilla-ice-cream"]["total_time_str"])
    print(recipes_dict["/recipes/ultimate-vanilla-ice-cream"]["total_time_int"])


if __name__ == "__main__":
    # get_seed_ingredients()
    # find_recipes(get_seed_ingredients())
    # scraping()
    # scrap_recipe_at()
    # analysis(print_unparsed_ingredients=False)

    # scrap_missing_info()
    # scrap_missing_info_for_recipes_DB()

    get_recipes_missing_total_time()
