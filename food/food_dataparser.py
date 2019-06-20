import csv
import json

def get_food_names(f = "./food/resources/dm/food_ratings.csv"):
    food_list = list()
    with open(f) as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        for row in csv_reader:
            food_list.append(row[2])

    return food_list[1:]


def get_dataset(f = "./food/resources/nlu/examples.json"):
    with open(f) as json_file:
        data = json.load(json_file)
        return data



if __name__ == "__main__":
    print(get_food_names())
