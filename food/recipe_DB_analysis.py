import spacy
import json
import csv
import matplotlib.pyplot as plt
import statistics as stats

X_recipes = 10
X_users = 10
json_recipes_users_DB_path = 'food/resources/recipes_DB/recipes_users_DB.json'
json_xUsers_Xrecipes_path = 'food/resources/recipes_DB/recipes'+X_recipes.__str__()+'_users'+X_users.__str__()+'_DB.json'
csv_xUsers_Xrecipes_path = 'food/resources/recipes_DB/recipes'+X_recipes.__str__()+'_users'+X_users.__str__()+'_DB.csv'
csv_xUsers_Xrecipes_path_0_1 = 'food/resources/recipes_DB/recipes'+X_recipes.__str__()+'_users'+X_users.__str__()+'_DB_0_1.csv'
csv_xUsers_Xrecipes_path_0_1_2 = 'food/resources/recipes_DB/recipes'+X_recipes.__str__()+'_users'+X_users.__str__()+'_DB_0_1_2.csv'


def recipes_users_DB_numbers():

    with open(json_recipes_users_DB_path, 'r') as f_recipe_user_data:
        content = json.load(f_recipe_user_data)
        recipes_dict = content['recipes_data']
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


    with open(csv_xUsers_Xrecipes_path, 'w') as fout:
        writer = csv.writer(fout)
        for row in csv_rows:
            writer.writerow(row)


    with open(csv_xUsers_Xrecipes_path_0_1, 'w') as fout:
        writer = csv.writer(fout)
        for row in csv_rows_0_1:
            writer.writerow(row)

    with open(csv_xUsers_Xrecipes_path_0_1_2, 'w') as fout:
        writer = csv.writer(fout)
        for row in csv_rows_0_1_2:
            writer.writerow(row)


def plot_recipes_avg_scores():
    recipes_to_look_at = list()
    with open(csv_xUsers_Xrecipes_path, 'r') as ratings_csv:
        reader = csv.reader(ratings_csv, delimiter=',')
        for row in reader:
            recipes_to_look_at.append(row[0])
    recipes_to_look_at = recipes_to_look_at[1:]

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
            print(recipe_id, all_ratings)
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

    plt.scatter(n_ratings_list, avg_ratings_list)
    plt.ylabel("Rating")
    plt.xlabel("Number of ratings")
    plt.title("Popularity of recipes")
    plt.show()


if __name__ == "__main__":
    # find_recipes(get_seed_ingredients())
    # n_users, n_recipes = recipes_users_DB_numbers()
    # format_user_item_matrix(n_users, n_recipes)
    # get_ratings_distribution()
    # plot_number_ratings_number_items()
    plot_recipes_avg_scores()