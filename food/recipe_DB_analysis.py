import spacy
import json
import csv
import matplotlib.pyplot as plt
import statistics as stats
import pandas as pd
import food.RS_utils as rs_utils

X_recipes = 10
X_users = 10
json_recipes_users_DB_path = 'food/resources/recipes_DB/recipes_users_DB.json'
json_xUsers_Xrecipes_path = 'food/resources/recipes_DB/recipes'+X_recipes.__str__()+'_users'+X_users.__str__()+'_DB.json'
csv_xUsers_Xrecipes_path = 'food/resources/recipes_DB/recipes'+X_recipes.__str__()+'_users'+X_users.__str__()+'_DB.csv'
csv_xUsers_Xrecipes_path_0_1 = 'food/resources/recipes_DB/recipes'+X_recipes.__str__()+'_users'+X_users.__str__()+'_DB_0_1.csv'
csv_xUsers_Xrecipes_path_0_1_2 = 'food/resources/recipes_DB/recipes'+X_recipes.__str__()+'_users'+X_users.__str__()+'_DB_0_1_2.csv'

no_nutrition_val_file_path = 'food/resources/recipes_DB/no_nutrition_val_recipes.txt'


def recipes_users_DB_numbers():

    with open(no_nutrition_val_file_path, 'r') as f_no_nutrition_val:
        r_no_nutrition_list = list()
        for line in f_no_nutrition_val:
            r_no_nutrition = '/' + line.split(' /')[1][:-1]
            r_no_nutrition_list.append(r_no_nutrition)

    with open(json_recipes_users_DB_path, 'r') as f_recipe_user_data:
        content = json.load(f_recipe_user_data)
        recipes_dict = content['recipes_data']

        print("Eliminating %d recipes with no nutritional info" % len(r_no_nutrition_list))
        for r_id in r_no_nutrition_list:
            recipes_dict[r_id] = None
            del recipes_dict[r_id]

        users_names = content['users_list']
        users_comments_data = content['users_data']
        # count_n_opinions_per_elt(users_comments_data)
        # recipes_with_X_or_more_comments = get_elts_with_5_or_more_ratings(recipes_dict, 'recipes')

        #eliminate users with less than 5 comments
        print("USERS")
        users_with_X_or_more_comments = get_elts_with_X_or_more_ratings(users_comments_data, X_users)
        new_users_comments_data = dict()
        for user_id, user_data in users_comments_data.items():
            if user_id in users_with_X_or_more_comments:
                new_users_comments_data[user_id] = user_data
        users_comments_data = new_users_comments_data

        n_users, n_recipes = len(users_names), len(recipes_dict.keys())
        difference = -1

        while difference != 0:

            # eliminate comments in recipes from users with less than 5 comments
            print("RECIPES")
            new_recipes_dict = dict()
            for recipe_id, recipe in recipes_dict.items():
                new_comments_list = list()
                for comment in recipe['comments']:
                    if comment['user_name'] in users_with_X_or_more_comments:
                        new_comments_list.append(comment)
                recipe['comments'] = new_comments_list
                recipe['n_comments'] = len(new_comments_list)
                if recipe['n_comments'] >= X_recipes:
                    new_recipes_dict[recipe_id] = recipe
            recipes_dict = new_recipes_dict

            #eliminate users
            recipes_with_X_or_more_comments = get_elts_with_X_or_more_ratings(recipes_dict, X_recipes, 'recipes')
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

    json_data = dict()
    json_data['recipes_data'] = recipes_dict
    json_data['users_data'] = users_comments_data
    with open(json_xUsers_Xrecipes_path, 'w') as fout:
        json.dump(json_data, fout, indent=True)

    return n_users, n_recipes


def count_n_opinions_per_elt(elts_data, key='n_comments'):
    elts_w_more_than_x_comments = dict()
    for _, data in elts_data.items():
        x = data[key]
        for i in range(1,x+1):
            if i not in elts_w_more_than_x_comments.keys():
                elts_w_more_than_x_comments[i] = 1
            else:
                elts_w_more_than_x_comments[i] += 1
    last_count = -1
    for i in range(1, 10000):
        if i in elts_w_more_than_x_comments.keys():
            x = elts_w_more_than_x_comments[i]
            if x != last_count:
                print("%d comments and more ---> %d" %(i, x))
                last_count = x
        else:
            break

def plot_number_ratings_number_items():
    with open(json_xUsers_Xrecipes_path, 'r') as fin:
        content = json.load(fin)
    recipes_data = content['recipes_data']
    n_ratings_to_n_items = dict()
    for recipe_id, recipe_data in recipes_data.items():
        n_comments = len(recipe_data['comments'])
        if n_comments not in n_ratings_to_n_items.keys():
            n_ratings_to_n_items[n_comments] = 1
        else:
            n_ratings_to_n_items[n_comments] += 1
    n_ratings_list, n_items_list = list(), list()
    for n_ratings, n_items in n_ratings_to_n_items.items():
        n_ratings_list.append(n_ratings)
        n_items_list.append(n_items)

    # fig = plt.figure()
    # ax = fig.add_axes([0,0,1,1])
    plt.scatter(n_items_list, n_ratings_list)
    plt.ylabel("Number of ratings")
    plt.xlabel("Number of items")
    plt.title("Popularity of recipes")
    plt.show()


def get_elts_with_X_or_more_ratings(elts_data, X=5, elt_name='users', key='n_comments'):
    elts = list()
    for elt, data in elts_data.items():
        x = data[key]
        if x >= X:
            elts.append(elt)
    print("%d %s with >= %d comments" % (len(elts), elt_name, X))
    return elts


def get_ratings_distribution():
    with open(json_xUsers_Xrecipes_path, 'r') as fin:
        content = json.load(fin)
    recipes_data = content['recipes_data']
    number_of_x = dict()
    for recipe_id, recipe_data in recipes_data.items():
        comments = recipe_data['comments']
        for comment in comments:
            rating = comment['n_stars']
            if rating not in number_of_x.keys():
                number_of_x[rating] = 1
            else:
                number_of_x[rating] += 1
    print("Ratings distribution:")
    sum_r, n_r = 0, 0
    for k, v in number_of_x.items():
        print("%d: %d" % (k, v))
        sum_r += k*v
        n_r += v
    print("Ratings average")
    print(float(sum_r) / n_r)


def format_user_item_matrix(n_users, n_recipes):
    with open(json_xUsers_Xrecipes_path, 'r') as fin:
        content = json.load(fin)
    csv_rows = list()
    csv_rows.append(['item', 'user', 'rating'])
    csv_rows_0_1 = list()
    csv_rows_0_1.append(['item', 'user', 'rating'])
    csv_rows_0_1_2 = list()
    csv_rows_0_1_2.append(['item', 'user', 'rating'])
    recipes_data = content['recipes_data']
    number_of_x = dict()
    for recipe_id, recipe_data in recipes_data.items():
        comments = recipe_data['comments']
        for comment in comments:
            user_id = comment['user_name']
            rating = comment['n_stars']
            if rating == 0:
                rating = 0.001
            rating_0_1 = 0 if rating <= 3.5 else 1
            rating_0_1_2 = 0 if rating == 0 else (1 if (rating == 1 or rating == 2 or rating == 3) else 2)
            csv_rows.append([recipe_id, user_id, rating])
            csv_rows_0_1.append([recipe_id, user_id, rating_0_1])
            csv_rows_0_1_2.append([recipe_id, user_id, rating_0_1_2])
            if rating not in number_of_x.keys():
                number_of_x[rating] = 1
            else:
                number_of_x[rating] += 1

    print("We collected %d ratings\nMatrix %.2f%% populated\n\nDistribution:" % (len(csv_rows), len(csv_rows)/float(n_users*n_recipes)*100))
    for k, v in number_of_x.items():
        print("%d: %d" % (k, v))


    # with open(csv_xUsers_Xrecipes_path, 'w') as fout:
    #     writer = csv.writer(fout)
    #     for row in csv_rows:
    #         writer.writerow(row)
    #
    #
    # with open(csv_xUsers_Xrecipes_path_0_1, 'w') as fout:
    #     writer = csv.writer(fout)
    #     for row in csv_rows_0_1:
    #         writer.writerow(row)
    #
    # with open(csv_xUsers_Xrecipes_path_0_1_2, 'w') as fout:
    #     writer = csv.writer(fout)
    #     for row in csv_rows_0_1_2:
    #         writer.writerow(row)


def get_recipes_avg_scores(plot_bool=False):
    recipes_to_look_at = list()
    with open(csv_xUsers_Xrecipes_path, 'r') as ratings_csv:
        reader = csv.reader(ratings_csv, delimiter=',')
        for row in reader:
            recipes_to_look_at.append(row[0])
    recipes_to_look_at = list(set(recipes_to_look_at[1:]))


    # scores from ALL the data we collected

    with open(json_recipes_users_DB_path, 'r') as json_data:
        content = json.load(json_data)
    recipes_data = content['recipes_data']

    data_ratings = dict()
    diff_our_rating_BBCGF_rating = dict()

    for recipe_id in recipes_to_look_at:
        recipe_comments = recipes_data[recipe_id]['comments']
        all_ratings = list()
        for comment in recipe_comments:
            all_ratings.append(comment['n_stars'])
            # if len(all_ratings) <= 15:
            #     print(all_ratings)
            #     print(float(sum(all_ratings))/len(all_ratings))
        n_ratings = len(all_ratings)
        if n_ratings > 1000:
            print(recipe_id, n_ratings)
        our_rating = float(sum(all_ratings))/n_ratings
        data_ratings[recipe_id] = [n_ratings, our_rating]
        diff = float(recipes_data[recipe_id]['ratings']['ratingValue']) - our_rating
        diff_our_rating_BBCGF_rating[recipe_id] = [diff, abs(diff)]
    # print(data_ratings.values())
    avg_ratings_list = [x[1] for x in data_ratings.values()]
    n_ratings_list = [x[0] for x in data_ratings.values()]
    print(stats.mean(avg_ratings_list))
    avg_diff = stats.mean([x[0] for x in diff_our_rating_BBCGF_rating.values()])
    avg_abs_diff = stats.mean([x[1] for x in diff_our_rating_BBCGF_rating.values()])
    print(avg_diff, avg_abs_diff)


    # Scores from the data we use for CF
    ratings_dict = dict()
    with open(csv_xUsers_Xrecipes_path, 'r') as ratings_csv:
        reader = csv.reader(ratings_csv, delimiter=',')
        first_row = True
        for row in reader:
            if not first_row:
                recipe, user, rating = row[0], row[1], row[2]
                rating = round(float(rating))
                if recipe not in ratings_dict.keys():
                    ratings_dict[recipe] = list()
                ratings_dict[recipe].append(rating)
            first_row = False

        for recipe, ratings in ratings_dict.items():
            ratings_dict[recipe] = [len(ratings), stats.mean(ratings)]

    if plot_bool:
        ratings_list = [x[1] for x in ratings_dict.values()]
        n_ratings_list = [x[0] for x in ratings_dict.values()]
        plt.scatter(n_ratings_list, ratings_list)
        plt.ylabel("Average rating")
        plt.xlabel("Number of ratings")
        plt.title("Popularity of recipes")
        plt.show()

    else:
        return ratings_dict


def get_datasets_stats(bool_plot=False):
    with open(json_recipes_users_DB_path, 'r') as fjson:
        content = json.load(fjson)
    all_recipes = content['recipes_data']

    ratings_dict = get_recipes_avg_scores()

    healthy_recipes_ids = ['/recipes/' + r for r in rs_utils.get_ids_healthy_recipes_coverage_set()]
    CF_recipes_ids = ['/recipes/' + r for r in rs_utils.get_ids_recipes_CF_coverage_set()]
    CFHbias_recipes_ids = ['/recipes/' + r for r in rs_utils.get_ids_CFhBias_recipes_coverage_set()]
    # print(healthy_recipes_ids)
    # print(CF_recipes_ids)

    x_CF_recipes, y_CF_recipes, h_CF_recipes, bbc_s_CF, bbc_rc_CF = list(), list(), list(), list(), list()
    x_CFHb_recipes, y_CFHb_recipes, h_CFHb_recipes, bbc_s_CFHb, bbc_rc_CFHb = list(), list(), list(), list(), list()
    x_healthy_recipes, y_healthy_recipes, h_healthy_recipes, bbc_s_healthy, bbc_rc_healthy = list(), list(), list(), list(), list()
    x_intersectionCFnH, y_intersectionCFnH, h_intersectionCFnH, bbc_s_intersectionCFnH, bbc_rc_intersectionCFnH = list(), list(), list(), list(), list()
    x_intersectionCFnCFHb, y_intersectionCFnCFHb, h_intersectionCFnCFHb, bbc_s_intersectionCFnCFHb, bbc_rc_intersectionCFnCFHb = list(), list(), list(), list(), list()
    x_intersectionHnCFHb, y_intersectionHnCFHb, h_intersectionHnCFHb, bbc_s_intersectionHnCFHb, bbc_rc_intersectionHnCFHb = list(), list(), list(), list(), list()
    x_other_recipes, y_other_recipes, h_other_recipes, bbc_s_others, bbc_rc_others = list(), list(), list(), list(), list()

    x_all, y_all, h_all, bbc_s_all, bbc_rc_all = list(), list(), list(), list(), list()

    for r, ratings_data in ratings_dict.items():
        # print(r)
        recipe = all_recipes[r]
        h = rs_utils.FSA_heathsclore(recipe)
        bbc_s = rs_utils.get_bbc_score(recipe)
        bbc_rc = rs_utils.get_bbc_rating_count(recipe)
        # --- 3 intersections to look at
        if r in healthy_recipes_ids and r in CF_recipes_ids:
            x_intersectionCFnH.append(ratings_data[0])
            x_CF_recipes.append(ratings_data[0])
            x_healthy_recipes.append(ratings_data[0])
            y_intersectionCFnH.append(ratings_data[1])
            y_CF_recipes.append(ratings_data[1])
            y_healthy_recipes.append(ratings_data[1])
            h_intersectionCFnH.append(h)
            h_CF_recipes.append(h)
            h_healthy_recipes.append(h)
            bbc_s_intersectionCFnH.append(bbc_s)
            bbc_s_CF.append(bbc_s)
            bbc_s_healthy.append(bbc_s)
            bbc_rc_intersectionCFnH.append(bbc_rc)
            bbc_rc_CF.append(bbc_rc)
            bbc_rc_healthy.append(bbc_rc)
        # --- 3 intersections to look at
        elif r in CFHbias_recipes_ids and r in CF_recipes_ids:
            x_intersectionCFnCFHb.append(ratings_data[0])
            x_CF_recipes.append(ratings_data[0])
            x_CFHb_recipes.append(ratings_data[0])
            y_intersectionCFnCFHb.append(ratings_data[1])
            y_CF_recipes.append(ratings_data[1])
            y_CFHb_recipes.append(ratings_data[1])
            h_intersectionCFnCFHb.append(h)
            h_CF_recipes.append(h)
            h_CFHb_recipes.append(h)
            bbc_s_intersectionCFnCFHb.append(bbc_s)
            bbc_s_CF.append(bbc_s)
            bbc_s_CFHb.append(bbc_s)
            on en est la
            bbc_rc_intersectionCFnH.append(bbc_rc)
            bbc_rc_CF.append(bbc_rc)
            bbc_rc_healthy.append(bbc_rc)
        elif r in healthy_recipes_ids:
            x_healthy_recipes.append(ratings_data[0])
            y_healthy_recipes.append(ratings_data[1])
            h_healthy_recipes.append(h)
            bbc_s_healthy.append(bbc_s)
            bbc_rc_healthy.append(bbc_rc)
        elif r in CF_recipes_ids:
            x_CF_recipes.append(ratings_data[0])
            y_CF_recipes.append(ratings_data[1])
            h_CF_recipes.append(h)
            bbc_s_CF.append(bbc_s)
            bbc_rc_CF.append(bbc_rc)
        else:
            x_other_recipes.append(ratings_data[0])
            y_other_recipes.append(ratings_data[1])
            h_other_recipes.append(h)
            bbc_s_others.append(bbc_s)
            bbc_rc_others.append(bbc_rc)

    if bool_plot:
        plt.scatter(x_other_recipes, y_other_recipes, c='grey', label="Others")
        plt.scatter(x_healthy_recipes, y_healthy_recipes, c='green', label="Healthy recipes")
        plt.scatter(x_CF_recipes, y_CF_recipes, c='blue', label='CF recipes')
        plt.scatter(x_intersectionCFnH, y_intersectionCFnH, c='orange', label="intersectionCFnH")
        plt.ylabel("Average rating")
        plt.xlabel("Number of ratings")
        plt.title("Popularity of recipes")
        plt.legend()
        plt.show()

    rs_utils.print_list_distribution(h_CF_recipes)

    x_all = x_CF_recipes + x_healthy_recipes + x_other_recipes
    x_all = rs_utils.diff_list(x_all, x_intersectionCFnH)
    print(len(x_all))

    y_all = y_CF_recipes + y_healthy_recipes + y_other_recipes
    y_all = rs_utils.diff_list(y_all, y_intersectionCFnH)

    h_all = h_CF_recipes + h_healthy_recipes + h_other_recipes
    h_all = rs_utils.diff_list(h_all, h_intersectionCFnH)

    bbc_s_all = bbc_s_CF + bbc_s_healthy + bbc_s_others
    bbc_s_all = rs_utils.diff_list(bbc_s_all, bbc_s_intersectionCFnH)

    bbc_rc_all = bbc_rc_CF + bbc_rc_healthy + bbc_rc_others
    bbc_rc_all = rs_utils.diff_list(bbc_rc_all, bbc_rc_intersectionCFnH)

    csv_rows = list()
    csv_rows.append(["Set", "Ratings Avg", "Ratings stddev", "Ratings Count Avg", "Ratings Count std", "BBC ratings Avg", "BBC ratings stddev", "BBC ratings c avg", "BBC ratings c std", "FSA scores avg", "FSA scores std"])
    csv_rows.append(["CF", stats.mean(y_CF_recipes), stats.stdev(y_CF_recipes), stats.mean(x_CF_recipes), stats.stdev(x_CF_recipes), stats.mean(bbc_s_CF), stats.stdev(bbc_s_CF), stats.mean(bbc_rc_CF), stats.stdev(bbc_rc_CF), stats.mean(h_CF_recipes), stats.stdev(h_CF_recipes)])
    csv_rows.append(["Healthy", stats.mean(y_healthy_recipes), stats.stdev(y_healthy_recipes), stats.mean(x_healthy_recipes), stats.stdev(x_healthy_recipes), stats.mean(bbc_s_healthy), stats.stdev(bbc_s_healthy), stats.mean(bbc_rc_healthy), stats.stdev(bbc_rc_healthy), stats.mean(h_healthy_recipes), stats.stdev(h_healthy_recipes)])
    csv_rows.append(["Other", stats.mean(y_other_recipes), stats.stdev(y_other_recipes), stats.mean(x_other_recipes), stats.stdev(x_other_recipes), stats.mean(bbc_s_others), stats.stdev(bbc_s_others), stats.mean(bbc_rc_others), stats.stdev(bbc_rc_others), stats.mean(h_other_recipes), stats.stdev(h_other_recipes)])
    csv_rows.append(["All", stats.mean(y_all), stats.stdev(y_all), stats.mean(x_all), stats.stdev(x_all), stats.mean(bbc_s_all), stats.stdev(bbc_s_all), stats.mean(bbc_rc_all), stats.stdev(bbc_rc_all), stats.mean(h_all), stats.stdev(h_all)])

    # with open("food/resources/recipes_DB/stats_RS_sets.csv", 'w') as csvf:
    #     csv_writer = csv.writer(csvf)
    #     for row in csv_rows:
    #         csv_writer.writerow(row)




if __name__ == "__main__":
    # find_recipes(get_seed_ingredients())
    # n_users, n_recipes = recipes_users_DB_numbers()
    # format_user_item_matrix(n_users, n_recipes)
    # get_ratings_distribution()
    # plot_number_ratings_number_items()
    # get_recipes_avg_scores()
    get_datasets_stats(bool_plot=True)
