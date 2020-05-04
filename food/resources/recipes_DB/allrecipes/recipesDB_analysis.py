import json
import csv
from food.resources.recipes_DB.allrecipes.nodejs_scrapper.consts import *

def get_DB_numbers():
    with open(json_reviews_file_path, 'r') as fjson:
        content = json.load(fjson)

    total_reviews = 0
    users = dict()
    for rid, ratings_data in content.items():
        total_reviews += ratings_data['n_reviews_collected']
        for review in ratings_data['reviews']:
            uid = review['id']
            if uid not in users.keys():
                users[uid] = 0
            users[uid] += 1

    print("Recipes:", len(content.keys()))
    print("Users:", len(users.keys()))
    print("Ratings:", total_reviews)


def get_matrix_data(users_comments_data, recipes_dict):
    n_reviews = 0
    for uid, udata in users_comments_data.items():
        n_reviews += udata['n_comments']

    n_recipes = len(recipes_dict.keys())
    n_users = len(users_comments_data.keys())
    print("Recipes:", n_recipes)
    print("Users:", n_users)
    print("Ratings:", n_reviews)
    print("Populated:", float(n_reviews) / (n_users * n_recipes))



def get_users_data():
    with open(json_reviews_file_path, 'r') as fjson:
        content = json.load(fjson)

    users = dict()
    for rid, ratings_data in content.items():
        for review in ratings_data['reviews']:
            uid = review['id']
            if uid not in users.keys():
                users[uid] = dict()
                users[uid]['n_comments'] = 0
                users[uid]['recipes_commented'] = list()
            users[uid]['n_comments'] += 1
            users[uid]['recipes_commented'].append(rid)

    return users


def get_elts_with_X_or_more_ratings(elts_data, X=5, elt_name='users', key='n_comments'):
    elts = list()
    for elt, data in elts_data.items():
        x = data[key]
        if x >= X:
            elts.append(elt)
    print("%d %s with >= %d comments" % (len(elts), elt_name, X))
    return elts


def reduce_DB_size():

    # with open(json_reviews_file_path, 'r') as f_recipe_user_data:
    #     recipes_dict = json.load(f_recipe_user_data)

    with open(json_users_data_10_reviews, 'r') as f_user_10:
        users_comments_data = json.load(f_user_10)

    with open(json_users_recipes_data_10reviews, 'r') as f_recipe_10:
        recipes_dict = json.load(f_recipe_10)

    # users_comments_data = get_users_data()
    users_names = users_comments_data.keys()

    #eliminate users with less than 5 comments
    print("USERS")
    users_with_X_or_more_comments = get_elts_with_X_or_more_ratings(users_comments_data, X_users)
    new_users_comments_data = dict()
    n_users = len(users_comments_data.keys())
    count = 0
    for user_id, user_data in users_comments_data.items():
        # if count % 10000 == 0:
        #     print("going through users:", count)
        if user_id in users_with_X_or_more_comments:
            new_users_comments_data[user_id] = user_data
        count += 1
    users_comments_data = new_users_comments_data

    # with open(json_users_data_10_reviews, 'w') as f10reviews:
    #     json.dump(users_comments_data, f10reviews, indent=True)

    n_users, n_recipes = len(users_names), len(recipes_dict.keys())
    difference = -1

    while difference != 0:

        # eliminate comments in recipes from users with less than 5 comments
        print("RECIPES")
        new_recipes_dict = dict()
        count = 0
        for recipe_id, recipe in recipes_dict.items():
            # if count % 1000 == 0:
            #     print("going through recipes:", count)
            new_comments_list = list()
            for review in recipe['reviews']:
                if review['id'] in users_with_X_or_more_comments:
                    new_comments_list.append(review)
            recipe['reviews'] = new_comments_list
            recipe['n_reviews_collected'] = len(new_comments_list)
            if recipe['n_reviews_collected'] >= X_recipes:
                new_recipes_dict[recipe_id] = recipe
            count += 1
        recipes_dict = new_recipes_dict

        # with open(json_users_recipes_data_10reviews, 'w') as f10revipesusersreviews:
        #     json.dump(recipes_dict, f10revipesusersreviews, indent=True)


        #eliminate users
        recipes_with_X_or_more_comments = get_elts_with_X_or_more_ratings(recipes_dict, X_recipes, 'recipes', 'n_reviews_collected')
        new_users_comments_data = dict()
        for user_id, user_data in users_comments_data.items():
            new_commented_recipes_list = list()
            # print(user_data['recipes_commented'])
            for r in user_data['recipes_commented']:
                if r in recipes_with_X_or_more_comments:
                    new_commented_recipes_list.append(r)
            user_data['n_comments'] = len(new_commented_recipes_list)
            if user_data['n_comments'] >= X_users:
                new_users_comments_data[user_id] = user_data

        users_comments_data = new_users_comments_data

        print("USERS")
        users_with_X_or_more_comments = get_elts_with_X_or_more_ratings(users_comments_data, X_users)

        new_n_users, new_n_recipes = len(users_comments_data.keys()), len(recipes_dict.keys())
        difference = (n_users - new_n_users) + (n_recipes - new_n_recipes)
        n_users, n_recipes = new_n_users, new_n_recipes

        print(difference)

    get_matrix_data(users_comments_data, recipes_dict)

    json_data = dict()
    json_data['recipes_data'] = recipes_dict
    json_data['users_data'] = users_comments_data
    with open(json_xUsers_Xrecipes_path, 'w') as fout:
        json.dump(json_data, fout, indent=True)


def create_user_item_matrix():
    with open(json_xUsers_Xrecipes_path, 'r') as fin:
        content = json.load(fin)
    recipes_data = content['recipes_data']
    csv_rows = list()
    if binary_bool:
        csv_rows.append(['item', 'user', 'rating', 'strength'])
    else:
        csv_rows.append(['item', 'user', 'rating'])
    number_of_x = dict()
    for recipe_id, recipe_data in recipes_data.items():
        reviews = recipe_data['reviews']
        for review in reviews:
            user_id = review['id']
            if binary_bool:
                strength = int(review['rating'])
                rating = 1
                csv_rows.append([recipe_id, user_id, rating, strength])
            else:
                rating = int(review['rating'])
                csv_rows.append([recipe_id, user_id, rating])
            if rating not in number_of_x.keys():
                number_of_x[rating] = 1
            else:
                number_of_x[rating] += 1
    total = len(csv_rows) - 1
    print("We collected %d ratings\n\nDistribution:" % total)
    for k, v in number_of_x.items():
        print("%d: %d (%.2f%%)" % (k, v, float(v)/total*100))

    path = csv_xUsers_Xrecipes_binary_path if binary_bool else csv_xUsers_Xrecipes_path
    with open(path, 'w') as fout:
        writer = csv.writer(fout)
        for row in csv_rows:
            writer.writerow(row)





if __name__ == "__main__":
    reduce_DB_size()
    create_user_item_matrix()
