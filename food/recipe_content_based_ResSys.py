import whiteboard_client as wbc
import helper_functions as helper
import json
import food.food_config as fc


class CBRSModule(wbc.WhiteBoardClient):
    def __init__(self, clientid, subscribes, publishes, resp_time=False):
        subscribes = helper.append_c_to_elts(subscribes, clientid)
        # publishes = {fc.USUAL_DM_MSG : publishes[0] + clientid, fc.RECIPE_DM_MSG: publishes[1] + clientid}
        publishes = publishes + clientid
        wbc.WhiteBoardClient.__init__(self, "CB-RS" + clientid, subscribes, publishes, resp_time)

        self.client_id = clientid


class ContentBasedRecSys():
    def __init__(self):
        with open('food/resources/dm/bbcgoodfood_scraped_recipes.json', 'r') as recipes_file:
            self.recipe_DB = json.load(recipes_file)
        self.id_to_recipe = dict()
        for recipe in self.recipe_DB:
            self.id_to_recipe[recipe['id']] = recipe

    def get_recipes_with_ingredient(self, ingredient):
        ingredient = ingredient.lower().strip()
        recipes_w_ingredient = list()
        for recipe in self.recipe_DB:
            if ingredient in recipe[fc.title].lower():
                recipes_w_ingredient.append(recipe)
            else:
                for r_ingredient in recipe[fc.ingredients]:
                    if ingredient in r_ingredient.lower():
                        recipes_w_ingredient.append(recipe)
        return recipes_w_ingredient

    def get_recipes_with_additional_characteristic(self, characteristic):
        recipes_to_return = list()
        for recipe in self.recipe_DB:
            if characteristic in recipe['additional_info']:
                recipes_to_return.append(recipe)
        return recipes_to_return

    def get_vegetarian_recipes(self):
        return self.get_recipes_with_additional_characteristic('Vegetarian')

    def get_vegan_recipes(self):
        return self.get_recipes_with_additional_characteristic('Vegan')

    def get_glutenfree_recipes(self):
        return self.get_recipes_with_additional_characteristic("Gluten-free")

    def get_dairyfree_recipes(self):
        return self.get_recipes_with_additional_characteristic('Dairy-free')

    def get_healthy_recipes(self):
        return self.get_recipes_with_additional_characteristic('Healthy')

    def get_recipes_ready_in_time(self, minutes_max):
        recipes_to_return = list()
        for recipe in self.recipe_DB:
            if minutes_max >= recipe['total_time']:
                recipes_to_return.append(recipe)
        return recipes_to_return

    def get_recipes(self, ingredient, total_time):
        r1 = [r['id'] for r in self.get_recipes_with_ingredient(ingredient)]
        r2 = [r['id'] for r in self.get_recipes_ready_in_time(total_time)]
        res_ids = list(set(r1) & set(r2))
        res_recipes = [self.id_to_recipe[id_r] for id_r in res_ids]
        return res_recipes
