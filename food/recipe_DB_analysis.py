import spacy
import json
import csv
import matplotlib.pyplot as plt
import statistics as stats
import pandas as pd
import food.RS_utils as rs_utils
import food.resources.recipes_DB.allrecipes.nodejs_scrapper.consts as consts



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




def get_ratings_distribution():
    with open(json_xUsers_Xrecipes_path_wo0ratings, 'r') as fin:
        content = json.load(fin)
    recipes_data = content['recipes_data']
    number_of_x = dict()
    total = 0
    for recipe_id, recipe_data in recipes_data.items():
        comments = recipe_data['comments']
        for comment in comments:
            rating = comment['n_stars']
            if rating not in number_of_x.keys():
                number_of_x[rating] = 1
            else:
                number_of_x[rating] += 1
            total += 1
    print("%d ratings (total)" % total)
    print("Ratings distribution:")
    sum_r, n_r = 0, 0
    for k, v in number_of_x.items():
        print("%d: %d (%.2f%%)" % (k, v, float(v)/ total * 100))
        sum_r += k*v
        n_r += v
    print("Ratings average")
    print(float(sum_r) / n_r)


def get_recipes_avg_scores(plot_bool=False):
    recipes_to_look_at = list()
    with open(csv_xUsers_Xrecipes_path_wo0ratings, 'r') as ratings_csv:
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
        n_ratings = len(all_ratings)
        our_rating = float(sum(all_ratings))/n_ratings
        data_ratings[recipe_id] = [n_ratings, our_rating]
        diff = float(recipes_data[recipe_id]['ratings']['ratingValue']) - our_rating
        diff_our_rating_BBCGF_rating[recipe_id] = [diff, abs(diff)]

    # Scores from the data we use for CF
    ratings_dict = dict()
    with open(csv_xUsers_Xrecipes_path_wo0ratings, 'r') as ratings_csv:
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
    with open(consts.json_xUsers_Xrecipes_path, 'r') as fjson:
        content = json.load(fjson)
    recipes_data = content['recipes_data']

    # ratings_dict = get_recipes_avg_scores()

    healthy_recipes_ids = rs_utils.get_ids_coverageHealth()
    CF_recipes_ids = rs_utils.get_ids_coveragePref()
    hybrid_recipes_ids = rs_utils.get_ids_coverageHybrid()

    data = dict()
    keys = [rs_utils.pref, rs_utils.hybrid, rs_utils.healthy, rs_utils.prefhybrid, rs_utils.prefhealthy, rs_utils.healthyhybrid, rs_utils.others, rs_utils._all]
    for k in keys:
        data[k] = dict()
        data[k][rs_utils.x], data[k][rs_utils.y], data[k][rs_utils.FSA_s], data[k][rs_utils.BBC_r], data[k][rs_utils.BBC_rc] = list(), list(), list(), list(), list()

    print("Going through %d recipes" % len(recipes_data.keys()))
    print("Coverage pref-based algo =", len(CF_recipes_ids))
    print("Coverage healthy-based algo =", len(healthy_recipes_ids))
    print("Coverage hybrid-based algo =", len(hybrid_recipes_ids))

    only_pref, only_hybrid, only_healthy = list(), list(), list()

    for rid, rdata in recipes_data.items():
        # print(r)
        x = rdata['n_reviews']
        y = rdata['rating']
        h = rdata['FSAscore']
        # bbc_r = rs_utils.get_bbc_score(recipe)
        # bbc_rc = rs_utils.get_bbc_rating_count(recipe)
        data_to_add_in = list()


        # --- 3 intersections to look at
        # in_intersection = False
        if rid in healthy_recipes_ids and rid in CF_recipes_ids:
            data_to_add_in.append(rs_utils.prefhealthy)
            # in_intersection = True
        if rid in hybrid_recipes_ids and rid in CF_recipes_ids:
            data_to_add_in.append(rs_utils.prefhybrid)
            # in_intersection = True
        if rid in hybrid_recipes_ids and rid in healthy_recipes_ids:
            data_to_add_in.append(rs_utils.healthyhybrid)
            # in_intersection = True

        # if not in_intersection:
        if rid in CF_recipes_ids:
            data_to_add_in.append(rs_utils.pref)
            # in_intersection = True
        if rid in healthy_recipes_ids:
            data_to_add_in.append(rs_utils.healthy)
            # in_intersection = True
        if rid in hybrid_recipes_ids:
            data_to_add_in.append(rs_utils.hybrid)
            # in_intersection = True

        # print(hybrid_recipes_ids)
        if len(data_to_add_in) == 1:
            if rs_utils.pref in data_to_add_in:
                only_pref.append(rid)
            elif rs_utils.healthy in data_to_add_in:
                only_healthy.append(rid)
            elif rs_utils.hybrid in data_to_add_in:
                only_hybrid.append(rid)

        # if not in_intersection:
        if not data_to_add_in:
            data_to_add_in = [rs_utils.others]


        data_to_add_in.append(rs_utils._all)

        data_to_add_in = list(set(data_to_add_in))


        for k in data_to_add_in:
            data[k][rs_utils.x].append(x)
            data[k][rs_utils.y].append(y)
            data[k][rs_utils.FSA_s].append(h)
            # data[k][rs_utils.BBC_r].append(bbc_r)
            # data[k][rs_utils.BBC_rc].append(bbc_rc)


    data_to_plot = [rs_utils._all, rs_utils.others, rs_utils.pref, rs_utils.healthy, rs_utils.hybrid, rs_utils.prefhealthy, rs_utils.healthyhybrid, rs_utils.prefhybrid]
    if bool_plot:
        for k in data_to_plot:
            if k == rs_utils.pref:
                sub_label = "\\"+len(only_pref).__str__()
            elif k == rs_utils.healthy:
                sub_label = "\\"+len(only_healthy).__str__()
            elif k == rs_utils.hybrid:
                sub_label = "\\"+len(only_hybrid).__str__()
            else:
                sub_label = ""
            label_str = k+" ("+len(data[k][rs_utils.x]).__str__()+sub_label+")"
            plt.scatter(data[k][rs_utils.x], data[k][rs_utils.y], c=rs_utils.colors[k], label=label_str)
        plt.ylabel("Average rating")
        plt.xlabel("Number of ratings")
        plt.title("Popularity of recipes")
        plt.legend()
        plt.show()

    print(len(data[rs_utils._all][rs_utils.x]))

    csv_rows = list()
    csv_rows.append(["Set", "Ratings Avg", "Ratings stddev", "Ratings Count Avg", "Ratings Count std", "BBC ratings Avg", "BBC ratings stddev", "BBC ratings c avg", "BBC ratings c std", "FSA scores avg", "FSA scores std"])
    for k in data_to_plot:
        new_row = list()
        new_row.append(k)

        m, std = rs_utils.get_mean(data[k][rs_utils.y]), rs_utils.get_std(data[k][rs_utils.y])
        # print(data[k][rs_utils.x])
        # print(m, std)
        new_row.append(m)
        new_row.append(std)

        new_row.append(rs_utils.get_mean(data[k][rs_utils.x]))
        new_row.append(rs_utils.get_std(data[k][rs_utils.x]))

        # new_row.append(rs_utils.get_mean(data[k][rs_utils.BBC_r]))
        # new_row.append(rs_utils.get_std(data[k][rs_utils.BBC_r]))
        #
        # new_row.append(rs_utils.get_mean(data[k][rs_utils.BBC_rc]))
        # new_row.append(rs_utils.get_std(data[k][rs_utils.BBC_rc]))

        new_row.append(rs_utils.get_mean(data[k][rs_utils.FSA_s]))
        new_row.append(rs_utils.get_std(data[k][rs_utils.FSA_s]))

        csv_rows.append(new_row)

    # csv_rows.append(["Healthy", stats.mean(y_healthy_recipes), stats.stdev(y_healthy_recipes), stats.mean(x_healthy_recipes), stats.stdev(x_healthy_recipes), stats.mean(bbc_s_healthy), stats.stdev(bbc_s_healthy), stats.mean(bbc_rc_healthy), stats.stdev(bbc_rc_healthy), stats.mean(h_healthy_recipes), stats.stdev(h_healthy_recipes)])
    # csv_rows.append(["Other", stats.mean(y_other_recipes), stats.stdev(y_other_recipes), stats.mean(x_other_recipes), stats.stdev(x_other_recipes), stats.mean(bbc_s_others), stats.stdev(bbc_s_others), stats.mean(bbc_rc_others), stats.stdev(bbc_rc_others), stats.mean(h_other_recipes), stats.stdev(h_other_recipes)])
    # csv_rows.append(["All", stats.mean(y_all), stats.stdev(y_all), stats.mean(x_all), stats.stdev(x_all), stats.mean(bbc_s_all), stats.stdev(bbc_s_all), stats.mean(bbc_rc_all), stats.stdev(bbc_rc_all), stats.mean(h_all), stats.stdev(h_all)])

    with open(csv_stats_path, 'w') as csvf:
        print("writing to", csv_stats_path)
        csv_writer = csv.writer(csvf)
        for row in csv_rows:
            csv_writer.writerow(row)




if __name__ == "__main__":
    # remove_0ratings()
    # recipes_users_DB_numbers()
    # find_recipes(get_seed_ingredients())
    # n_users, n_recipes = recipes_users_DB_numbers()
    # format_user_item_matrix(n_users, n_recipes)
    # get_ratings_distribution()
    # plot_number_ratings_number_items()
    # get_recipes_avg_scores()

    get_datasets_stats(bool_plot=True)
