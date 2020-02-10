from recipe_scrapers import scrape_me
import json
import food.food_dataparser as food_dataparser
import dataparser
import food.NLU as NLU
import spacy
import nlu_helper_functions as nlu_helper
import re
import food.food_config as fc

to_scrap = [
    #test
    # 'https://www.bbcgoodfood.com/recipes/goan-style-vegetable-curry-kitchari',
    # chicken
    'https://www.bbcgoodfood.com/recipes/caesar-salad-crispy-chicken', # 5min, salad
    'https://www.bbcgoodfood.com/recipes/sweet-potato-chicken-curry',  # curry
    'https://www.bbcgoodfood.com/recipes/summer-winter-chicken', # first res
    'https://www.bbcgoodfood.com/recipes/chicken-noodle-soup', # soup
    'https://www.bbcgoodfood.com/recipes/crispy-greek-style-pie', # pie
    'https://www.bbcgoodfood.com/recipes/easiest-ever-paella', # paella
    'https://www.bbcgoodfood.com/recipes/chicken-breast-avocado-salad', # salad, chicken breast
    'https://www.bbcgoodfood.com/recipes/moroccan-chicken-one-pot', #healthy
    'https://www.bbcgoodfood.com/recipes/italian-stuffed-chicken', # GF
    'https://www.bbcgoodfood.com/recipes/7997/sticky-chicken-with-sherry-almonds-and-dates', # dairy free
    'https://www.bbcgoodfood.com/recipes/roast-chicken-roots', #GF
    'https://www.bbcgoodfood.com/recipes/quick-chicken-hummus-bowl', # 5min
    'https://www.bbcgoodfood.com/recipes/chilli-chicken-honey-soy', # 5min
    
    #avocado
    'https://www.bbcgoodfood.com/recipes/linguine-avocado-tomato-lime', # vegan
    'https://www.bbcgoodfood.com/recipes/avocado-panzanella', # vegan

    # beef
    'https://www.bbcgoodfood.com/recipes/beef-stroganoff-herby-pasta', # 30 min
    'https://www.bbcgoodfood.com/recipes/beef-bourguignon-celeriac-mash', # 3h
    'https://www.bbcgoodfood.com/recipes/crispy-chilli-beef', #40min
    'https://www.bbcgoodfood.com/recipes/quick-beef-broccoli-noodles', # 20min

    # broccoli
    'https://www.bbcgoodfood.com/recipes/tortellini-pesto-broccoli', # 10min
    'https://www.bbcgoodfood.com/recipes/parmesan-broccoli', # vegetarian
    'https://www.bbcgoodfood.com/recipes/broccoli-stilton-soup', # soup

    # cabbage
    'https://www.bbcgoodfood.com/recipes/baked-haddock-cabbage-risotto',
    'https://www.bbcgoodfood.com/recipes/gujarati-cabbage-coconut-potato',
    'https://www.bbcgoodfood.com/recipes/squash-cabbage-sabzi',

    # cauloflower
    'https://www.bbcgoodfood.com/recipes/cauliflower-cheese-0',
    'https://www.bbcgoodfood.com/recipes/cauliflower-rice', # 10 min
    'https://www.bbcgoodfood.com/recipes/roasted-cauliflower-garlic-bay-lemon', #vegan

    # cheese
    'https://www.bbcgoodfood.com/recipes/gnocchi-mushrooms-blue-cheese',
    'https://www.bbcgoodfood.com/recipes/leek-cheese-bacon-tart', #tart
    'https://www.bbcgoodfood.com/recipes/goats-cheese-thyme-stuffed-chicken',

    # chillies
    'https://www.bbcgoodfood.com/recipes/red-lentil-chickpea-chilli-soup',
    'https://www.bbcgoodfood.com/recipes/chilli-cheese-omelette', # 10min
    'https://www.bbcgoodfood.com/recipes/stir-fried-curly-kale-chilli-garlic', # 10min, vegan

    # eggs
    'https://www.bbcgoodfood.com/recipes/scrambled-egg-stir-fry', # 10min
    'https://www.bbcgoodfood.com/recipes/veggie-egg-fried-rice', # vegetarian
    'https://www.bbcgoodfood.com/recipes/baked-eggs-spinach-tomato', # GF

    # fish
    'https://www.bbcgoodfood.com/recipes/thai-style-steamed-fish',
    'https://www.bbcgoodfood.com/recipes/super-quick-fish-curry',
    'https://www.bbcgoodfood.com/recipes/fish-tacos', # healthy

    # salmon
    'https://www.bbcgoodfood.com/recipes/pasta-salmon-peas',
    'https://www.bbcgoodfood.com/recipes/superhealthy-salmon-burgers',
    'https://www.bbcgoodfood.com/recipes/salmon-spinach-tartare-cream',
]


def scraping():
    recipes_list = list()

    for i, url in enumerate(to_scrap):
        print(url)
        recipe = dict()
        # give the url as a string, it can be url from any site listed below
        scraper = scrape_me(url)

        recipe['id'] = i
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

        recipes_list.append(recipe)
    # print(scraper.links())

    # print(recipes_list)

    with open('food/resources/dm/bbcgoodfood_scraped_recipes.json', 'w') as f:
        json.dump(recipes_list, f, indent=True)



def analysis(print_unparsed_ingredients=False):
    ingredients_found = list()
    spacy_nlp = spacy.load("en_core_web_sm")

    food_list = food_dataparser.extensive_food_DBs.all_foods_list
    voc = dataparser.parse_voc(f_domain_voc="food/resources/nlu/food_voc.json")
    total, correctely_parsed = 0, 0
    all_ingredients = dict()

    with open('food/resources/dm/bbcgoodfood_scraped_recipes.json', 'r') as f:
        content = json.load(f)
        for recipe in content:

            # calculating healthiness values
            healthiness_score = 0
            for elt in fc.nutrition_elements:
                # print(recipe['nutrition'][elt])
                elt_quantity = float(recipe['nutrition'][elt].replace('g','') if 'g' in recipe['nutrition'][elt] else recipe['nutrition'][elt])
                if elt_quantity <= fc.RECOMMENDED_VALUES[elt][fc.low_to_medium]:
                    healthiness_score += 2
                elif elt_quantity <= fc.RECOMMENDED_VALUES[elt][fc.medium_to_high]:
                    healthiness_score += 1


            print("Parsing %s --> %d health score" % (recipe['title'], healthiness_score))


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

    print("Ingredients succesfully parsed: %.2f" % (float(correctely_parsed) / total))

    for category, ingredients_dict in all_ingredients.items():
        if category in ['dishes', 'unknown', 'dairy', 'vegetables', 'meat', 'eggs', 'gourds', 'pasta', 'fish']:
            print("\n---------------")
            print(category)
            for ingredient, found_in_n_recipes in ingredients_dict.items():
                print(ingredient, found_in_n_recipes)


if __name__ == "__main__":
    # scraping()
    analysis(print_unparsed_ingredients=False)
