from recipe_scrapers import scrape_me
import json
import food.food_dataparser as food_dataparser
import dataparser
import food.NLU as NLU
import spacy
import nlu_helper_functions as nlu_helper
import re
import food.food_config as fc
from bs4 import BeautifulSoup
# from selenium import webdriver
import requests
import sys
import os

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.7) Gecko/2009021910 Firefox/3.0.7'
}

INGREDIENTS_CATEGORIES_TO_SCRAP = ['vegetables', 'fruits', 'pulses', 'gourds', 'meat', 'fish', 'eggs', 'dishes', 'pasta', 'cereals']

explored_ingredients = list()
recipes_to_ratings = dict()
ingredients_to_recipes = dict()
recipes_to_scrap_list = list()


if os.path.isfile('food/resources/recipes_DB/recipes_users_DB.json'):
    with open('food/resources/recipes_DB/recipes_users_DB.json', 'r') as f_recipe_user_data:
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
    # chicken
    # 'https://www.bbcgoodfood.com/recipes/caesar-salad-crispy-chicken', # 5min, salad
    # 'https://www.bbcgoodfood.com/recipes/sweet-potato-chicken-curry',  # curry
    # 'https://www.bbcgoodfood.com/recipes/summer-winter-chicken', # first res
    # 'https://www.bbcgoodfood.com/recipes/chicken-noodle-soup', # soup
    # 'https://www.bbcgoodfood.com/recipes/crispy-greek-style-pie', # pie
    # 'https://www.bbcgoodfood.com/recipes/easiest-ever-paella', # paella
    # 'https://www.bbcgoodfood.com/recipes/chicken-breast-avocado-salad', # salad, chicken breast
    # 'https://www.bbcgoodfood.com/recipes/moroccan-chicken-one-pot', #healthy
    # 'https://www.bbcgoodfood.com/recipes/italian-stuffed-chicken', # GF
    # 'https://www.bbcgoodfood.com/recipes/7997/sticky-chicken-with-sherry-almonds-and-dates', # dairy free
    # 'https://www.bbcgoodfood.com/recipes/roast-chicken-roots', #GF
    # 'https://www.bbcgoodfood.com/recipes/quick-chicken-hummus-bowl', # 5min
    # 'https://www.bbcgoodfood.com/recipes/chilli-chicken-honey-soy', # 5min
    #
    # #avocado
    # 'https://www.bbcgoodfood.com/recipes/linguine-avocado-tomato-lime', # vegan
    # 'https://www.bbcgoodfood.com/recipes/avocado-panzanella', # vegan
    #
    # # beef
    # 'https://www.bbcgoodfood.com/recipes/beef-stroganoff-herby-pasta', # 30 min
    # 'https://www.bbcgoodfood.com/recipes/beef-bourguignon-celeriac-mash', # 3h
    # 'https://www.bbcgoodfood.com/recipes/crispy-chilli-beef', #40min
    # 'https://www.bbcgoodfood.com/recipes/quick-beef-broccoli-noodles', # 20min
    #
    # # broccoli
    # 'https://www.bbcgoodfood.com/recipes/tortellini-pesto-broccoli', # 10min
    # 'https://www.bbcgoodfood.com/recipes/parmesan-broccoli', # vegetarian
    # 'https://www.bbcgoodfood.com/recipes/broccoli-stilton-soup', # soup
    #
    # # cabbage
    # 'https://www.bbcgoodfood.com/recipes/baked-haddock-cabbage-risotto',
    # 'https://www.bbcgoodfood.com/recipes/gujarati-cabbage-coconut-potato',
    # 'https://www.bbcgoodfood.com/recipes/squash-cabbage-sabzi',
    #
    # # cauloflower
    # 'https://www.bbcgoodfood.com/recipes/cauliflower-cheese-0',
    # 'https://www.bbcgoodfood.com/recipes/cauliflower-rice', # 10 min
    # 'https://www.bbcgoodfood.com/recipes/roasted-cauliflower-garlic-bay-lemon', #vegan
    #
    # # cheese
    # 'https://www.bbcgoodfood.com/recipes/gnocchi-mushrooms-blue-cheese',
    # 'https://www.bbcgoodfood.com/recipes/leek-cheese-bacon-tart', #tart
    # 'https://www.bbcgoodfood.com/recipes/goats-cheese-thyme-stuffed-chicken',
    #
    # # chillies
    # 'https://www.bbcgoodfood.com/recipes/red-lentil-chickpea-chilli-soup',
    # 'https://www.bbcgoodfood.com/recipes/chilli-cheese-omelette', # 10min
    # 'https://www.bbcgoodfood.com/recipes/stir-fried-curly-kale-chilli-garlic', # 10min, vegan
    #
    # # eggs
    # 'https://www.bbcgoodfood.com/recipes/scrambled-egg-stir-fry', # 10min
    # 'https://www.bbcgoodfood.com/recipes/veggie-egg-fried-rice', # vegetarian
    # 'https://www.bbcgoodfood.com/recipes/baked-eggs-spinach-tomato', # GF
    #
    # # fish
    # 'https://www.bbcgoodfood.com/recipes/thai-style-steamed-fish',
    # 'https://www.bbcgoodfood.com/recipes/super-quick-fish-curry',
    # 'https://www.bbcgoodfood.com/recipes/fish-tacos', # healthy
    #
    # # salmon
    # 'https://www.bbcgoodfood.com/recipes/pasta-salmon-peas',
    # 'https://www.bbcgoodfood.com/recipes/superhealthy-salmon-burgers',
    # 'https://www.bbcgoodfood.com/recipes/salmon-spinach-tartare-cream',
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
    with open('food/resources/recipes_DB/recipes_users_DB.json', 'w') as f:
        json.dump(recipes_users_data, f, indent=True)


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




if __name__ == "__main__":
    get_seed_ingredients()
    # find_recipes(get_seed_ingredients())
    # scraping()
    # scrap_recipe_at()
    # analysis(print_unparsed_ingredients=False)
