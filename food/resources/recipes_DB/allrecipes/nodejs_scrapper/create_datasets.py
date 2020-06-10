import json
import csv
import food.resources.recipes_DB.allrecipes.nodejs_scrapper.consts as consts
import copy
import food.RS_utils as rs_utils

def create_json_10reviews():
    with open(consts.json_fullDB_path, 'r') as fjson:
        content = json.load(fjson)
    rdata = content['recipes_data']
    udata = content['users_data']
    rdata10 = dict()
    udata10 = dict()
    for rid, rdict in rdata.items():
        if rdict['reviews']['n_reviews_collected'] >= 10:
            rdata10[rid] = copy.copy(rdict['recipe_info'])
            rdata10[rid]['n_reviews'] = rdict['reviews']['n_reviews_collected']
            # print(rdata10[rid])
            del rdata10[rid]['n_ratings']
            rdata10[rid]['reviews'] = rdict['reviews']['reviews']
            sum_reviews = 0
            for review in rdata10[rid]['reviews']:
                # print(review)
                sum_reviews += int(review['rating'])
            rdata10[rid]['rating'] = float(sum_reviews) / len(rdata10[rid]['reviews'])
    for uid, udict in udata.items():
        # print(udict)
        if udict['n_comments'] >= 10:
            udata10[uid] = udict
    with open(consts.json_recipes_data_10reviews, 'w') as f:
        json.dump(rdata10, f, indent=True)
    with open(consts.json_users_data_10_reviews, 'w') as f:
        json.dump(udata10, f, indent=True)
    print("Wrote files:", consts.json_recipes_data_10reviews, consts.json_users_data_10_reviews)


def get_DB_numbers():
    with open(consts.json_reviews_file_path, 'r') as fjson:
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
    with open(consts.json_reviews_file_path, 'r') as fjson:
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

    with open(consts.json_users_data_10_reviews, 'r') as f_user_10:
        users_comments_data = json.load(f_user_10)

    with open(consts.json_recipes_data_10reviews, 'r') as f_recipe_10:
        recipes_dict = json.load(f_recipe_10)

    users_names = users_comments_data.keys()

    #eliminate users with less than 5 comments
    print("USERS")
    users_with_X_or_more_comments = get_elts_with_X_or_more_ratings(users_comments_data, consts.X_users)
    new_users_comments_data = dict()
    count = 0
    for user_id, user_data in users_comments_data.items():
        if user_id in users_with_X_or_more_comments:
            new_users_comments_data[user_id] = user_data
        count += 1
    users_comments_data = new_users_comments_data

    n_users, n_recipes = len(users_names), len(recipes_dict.keys())
    difference = -1

    while difference != 0:

        # eliminate comments in recipes from users with less than 5 comments
        print("RECIPES")
        new_recipes_dict = dict()
        count = 0
        for recipe_id, recipe in recipes_dict.items():
            new_comments_list = list()
            for review in recipe['reviews']:
                # print(review)
                if review['id'] in users_with_X_or_more_comments:
                    new_comments_list.append(review)
            recipe['reviews'] = new_comments_list
            recipe['n_reviews_collected'] = len(new_comments_list)
            if recipe['n_reviews_collected'] >= consts.X_recipes:
                new_recipes_dict[recipe_id] = recipe
            count += 1
        recipes_dict = new_recipes_dict

        #eliminate users
        recipes_with_X_or_more_comments = get_elts_with_X_or_more_ratings(recipes_dict, consts.X_recipes, 'recipes', 'n_reviews_collected')
        new_users_comments_data = dict()
        for user_id, user_data in users_comments_data.items():
            new_commented_recipes_list = list()
            # print(user_data['recipes_commented'])
            for r in user_data['recipes_commented']:
                if r in recipes_with_X_or_more_comments:
                    new_commented_recipes_list.append(r)
            user_data['n_comments'] = len(new_commented_recipes_list)
            user_data['recipes_commented'] = new_commented_recipes_list
            if user_data['n_comments'] >= consts.X_users:
                new_users_comments_data[user_id] = user_data

        users_comments_data = new_users_comments_data

        print("USERS")
        users_with_X_or_more_comments = get_elts_with_X_or_more_ratings(users_comments_data, consts.X_users)

        new_n_users, new_n_recipes = len(users_comments_data.keys()), len(recipes_dict.keys())
        difference = (n_users - new_n_users) + (n_recipes - new_n_recipes)
        n_users, n_recipes = new_n_users, new_n_recipes

        print(difference)

    get_matrix_data(users_comments_data, recipes_dict)

    json_data = dict()
    json_data['recipes_data'] = recipes_dict
    json_data['users_data'] = users_comments_data
    with open(consts.json_xUsers_Xrecipes_path, 'w') as fout:
        json.dump(json_data, fout, indent=True)


def create_user_item_matrix():
    with open(consts.json_xUsers_Xrecipes_path, 'r') as fin:
        content = json.load(fin)
    recipes_data = content['recipes_data']
    csv_rows = list()
    csv_rows.append(['item', 'user', 'rating'])
    number_of_x = dict()
    for recipe_id, recipe_data in recipes_data.items():
        reviews = recipe_data[consts.reviews]
        for review in reviews:
            user_id = review[consts.uid]
            rating = int(review[consts.rating])
            csv_rows.append([recipe_id, user_id, rating])
            if rating not in number_of_x.keys():
                number_of_x[rating] = 1
            else:
                number_of_x[rating] += 1
    total = len(csv_rows) - 1
    print("We collected %d ratings\n\nDistribution:" % total)
    for k, v in number_of_x.items():
        print("%d: %d (%.2f%%)" % (k, v, float(v)/total*100))

    path = consts.csv_xUsers_Xrecipes_path
    with open(path, 'w') as fout:
        writer = csv.writer(fout)
        for row in csv_rows:
            writer.writerow(row)

def save_FSAscore():
    with open(consts.json_xUsers_Xrecipes_path, 'r') as fjson:
        content = json.load(fjson)
    recipes_list = content['recipes_data'].values()
    for recipe in recipes_list:
        FSA_score = rs_utils.FSA_heathsclore(recipe)
        recipe['FSAscore'] = FSA_score
    # rid = list(content['recipes_data'].keys())[0]
    # r = content['recipes_data'][rid]
    # print(r)
    with open(consts.json_xUsers_Xrecipes_path, 'w') as fjson:
        json.dump(content, fjson, indent=True)
    print("Wrote Heath scores in", consts.json_xUsers_Xrecipes_path)


def json_list_dataset_rids():
    with open(consts.json_xUsers_Xrecipes_path, 'r') as fjson:
        content = json.load(fjson)
    rids_list = list(content['recipes_data'].keys())
    with open(consts.json_rids_list_xUsers_Xrecipes_path, 'w') as fout:
        json.dump(rids_list, fout, indent=True)


def merge_descriptions_to_main():
    with open(consts.json_descriptions_xUsers_Xrecipes_path, 'r') as fdescriptions:
        descriptions = json.load(fdescriptions)
    with open(consts.json_xUsers_Xrecipes_path, 'r') as fjson:
        content = json.load(fjson)
    recipes_data = content['recipes_data']
    for rid, rdata in recipes_data.items():
        if rid not in descriptions.keys():
            print("No description for %s" % rid)
        else:
            rdata['description'] = descriptions[rid]
    # first_rid = list(recipes_data.keys())[0]
    # first_rdtata = recipes_data[first_rid]
    # print(first_rdtata)
    content['recipes_data'] = recipes_data
    with open(consts.json_xUsers_Xrecipes_path, 'w') as fjson:
        json.dump(content, fjson, indent=True)

if __name__ == "__main__":
    # create_json_10reviews()
    # reduce_DB_size()
    create_user_item_matrix()
    # save_FSAscore()
    # json_list_dataset_rids()
    # merge_descriptions_to_main()
