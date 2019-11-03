import csv
import json

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


def get_dataset(f = "./food/resources/nlu/examples.json"):
    with open(f) as json_file:
        data = json.load(json_file)
        return data



if __name__ == "__main__":
    print(get_food_names())
