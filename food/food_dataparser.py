import csv
import json
import pandas
# from ca_logging import log
import food.food_config as fc

def get_food_names(f = "./food/resources/dm/food_ratings.csv"):
    food_list = list()
    with open(f) as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        for row in csv_reader:
            ingredient = row[2]
            ingredient = ingredient.replace("dish", "")
            ingredient = ingredient.replace("side", "")
            ingredient = ingredient.replace("meal", "")
            ingredient = ingredient.replace("(only)", "")
            ingredient = ingredient.strip()
            food_list.append(ingredient)
    return food_list[1:]


def get_dataset(f="food/resources/nlu/datacollection_examples.json"):
    with open(f) as json_file:
        data = json.load(json_file)
        return data

def generate_examples_dataset_json_from_annotated_csv(csv_path):
    json_list = list()
    with open(csv_path, 'r') as fcsv:
        csv_lines = csv.reader(fcsv)
        for line in csv_lines:
            # print(line)
            if all(elt == '' for elt in line[4:]) and line[3]:
                # print(line[4:])
                str_user_intent = line[3].replace("'", '"')
                str_user_intent = str_user_intent.replace("None", "null")
                str_user_intent = str_user_intent.replace("True", "true")
                str_user_intent = str_user_intent.replace("False", "false")
                # print(str_user_intent)
                json_user_intent = json.loads(str_user_intent)
                json_list.append({"id": line[0], "conv_stage": line[1], "utterance": line[2], "user_intent": json_user_intent})
    with open("food/resources/nlu/datacollection_examples.json", "w") as fjson:
        json.dump(json_list, fjson)

def parse_healthiness_quantifiers_csv(csv_path):
    json_list = list()
    id = 0
    with open(csv_path, 'r') as fcsv:
        csv_lines = csv.reader(fcsv)
        for line in csv_lines:
            json_user_intent = {"intent": "inform", "entity": float(line[1]), "entity_type": "healthy", "polarity": None}
            json_list.append({"id": id, "conv_stage": "request(healthy)", "utterance": line[0], "user_intent": json_user_intent})
            id += 1
    with open("food/resources/nlu/datacollection_examples_quantifiers.json", "w") as fjson:
        json.dump(json_list, fjson)



class Extensive_food_DBs:
    """Singleton class"""
    __instance = None

    @staticmethod
    def getInstance():
        """
        :return: the unique object
        """
        if Extensive_food_DBs.__instance == None:
            Extensive_food_DBs()
        return  Extensive_food_DBs.__instance


    def __init__(self):
        """
        This constructor in virtually private.
        :param domain:
        """
        if Extensive_food_DBs.__instance != None:
            error_msg = "Singleton Class: contructor should not be called. Use Modules.getInstance()"
            # log.error(error_msg)
            print(error_msg)
        else:
            Extensive_food_DBs.__instance = self
            self.food_to_category = {}
            self.category_to_foods = {}
            self.all_foods_list = list()

            self.category_to_simplified_category = {
                'coffee and coffee products': "coffee",
                'milk and milk products': "dairy",
                'cocoa and cocoa products': "cocoa",
                'fats and oils': "oils",
                'animal foods' : "meat",
                'herbs and spices': "spices",
                'confectioneries': "sweets",
                'cereals and cereal products': "cereals",
                'aquatic foods': "fish"
            }

            self.load_extensive_food_DBs()

            # for category, foods in self.category_to_foods.items():
            #     print(category, foods)

    def get_simplified_category(self, category):
        if category in self.category_to_simplified_category.keys():
            return self.category_to_simplified_category[category]
        else:
            return category

    def load_extensive_food_DBs(self):
        df = pandas.read_csv(fc.EXTENSIVE_FOOD_DB_PATH, encoding="ISO-8859-1")
        for index, row in df.iterrows():
            if index > 0:
                food_name = row["name"].lower()
                category = self.get_simplified_category(row["food_group"].lower())
                if "chicken" in food_name:
                    print(food_name, category)
                self.save_to_extensive_foods_DBs(food_name, category)
        all_categories = set(self.food_to_category.values())
        # print(all_categories)
        # for category, foods in self.category_to_foods.items():
        #     print(category, foods)
        self.post_processing()
        for category, foods in self.category_to_foods.items():
            self.all_foods_list += foods
            self.all_foods_list.append(category)
        # print(self.all_foods_list)

    def save_to_extensive_foods_DBs(self, food_name, category):
        chicken = "chicken" in food_name
        food_name_words_list = food_name.split()
        if len(food_name) > 3:# and len(food_name_words_list) < 3:
            if "(" in food_name and ")" in food_name:
                in_parentehses = food_name[food_name.find("(")+1:food_name.find(")")]
                splited_at_comma = in_parentehses.split(',')
                sub_foods = [food_name[:food_name.find('(')-1].strip()] + [w.strip() for w in splited_at_comma]
                if chicken:
                    print(sub_foods)
                for f in sub_foods:
                    self.save_to_extensive_foods_DBs(f, category)
            elif "," in food_name:
                splited_at_comma = food_name.split(',')
                sub_foods = [w.strip() for w in splited_at_comma]
                for f in sub_foods:
                    self.save_to_extensive_foods_DBs(f, category)
            else:
                self.food_to_category[food_name] = category
                if category not in self.category_to_foods.keys():
                    self.category_to_foods[category] = list()
                if food_name not in self.category_to_foods[category]:
                    self.category_to_foods[category].append(food_name)
                if len(food_name_words_list) == 2:
                    second_word = food_name_words_list[1]
                    if len(second_word) > 3 and "food" not in second_word:
                        self.food_to_category[second_word] = category
                        if second_word not in self.category_to_foods[category]:
                            self.category_to_foods[category].append(second_word)

    def remove_foods_from_list(self, to_remove_list, list_to_remove_from):
        for elt in to_remove_list:
            if elt in list_to_remove_from:
                list_to_remove_from.remove(elt)

    def add_foods_to_list(self, to_add_to_list, list_to_add_to):
        for elt in to_add_to_list:
            list_to_add_to.append(elt)

    def post_processing(self):
        for category, foods in self.category_to_foods.items():
            if category == "vegetables":
                to_remove = ['rape', 'cress', 'stalks', "leaves", "var.", "shoots", "tree", "flower"]
                to_add = ["celery", "zucchini", "pumpkin", "squash", "cucumber", "butternut", "peas", "beans"]
                self.remove_foods_from_list(to_remove, foods)
                self.add_foods_to_list(to_add, foods)
            elif category == "spices":
                to_remove = ["celery", "turnip", "savory", "onion", "leaves", "nuts", "powder", "tree", "preserve", "salad"]
                to_add = ["vervain"]
                self.remove_foods_from_list(to_remove, foods)
                self.add_foods_to_list(to_add, foods)
            elif category == "fruits":
                to_remove = ["var.", "hybrid", "leaves", "nuts", "powder", "tree", "preserve", "salad"]
                to_add = ["watermelon", "melon"]
                self.remove_foods_from_list(to_remove, foods)
                self.add_foods_to_list(to_add, foods)
            elif category == "fish":
                to_remove = ["halibut/turbot", "moss", "smelt", "cucumber", "sucker"]
                to_add = ["halibut", "turbot"]
                self.remove_foods_from_list(to_remove, foods)
                self.add_foods_to_list(to_add, foods)

    def get_category(self, food):
        if food in self.food_to_category.keys():
            return self.food_to_category[food]

    def is_category(self, food):
        if food in list(self.category_to_foods.keys()):
            return True
        return False

    def is_food_in_category(self, food, category):
        if food in self.food_to_category.keys():
            return self.food_to_category[food] == category
        return False

extensive_food_DBs = Extensive_food_DBs.getInstance()

if __name__ == "__main__":
    # parse_healthiness_quantifiers_csv("food/resources/nlu/quantifiers.csv")
    generate_examples_dataset_json_from_annotated_csv("food/resources/data_collection/NLU_analyzed.csv")
