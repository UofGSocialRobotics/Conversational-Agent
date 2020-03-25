import pandas as pd
from surprise import Reader
import statistics as stats
import math
from collections import defaultdict
import csv
from food.ranking_eval import nDCGatK, MAPatK
import numpy as np
import random
import time

from surprise import Dataset
from surprise import SVD, NMF
from surprise.model_selection import KFold
from surprise import KNNWithMeans
from surprise.model_selection import GridSearchCV
from surprise.prediction_algorithms.predictions import Prediction

from sklearn.metrics import mean_squared_error, mean_absolute_error


flatten = lambda l: [item for sublist in l for item in sublist]

BBCGoodFood_dataset_str = 'BBCGoodFood'
movieLens_dataset_str = 'MovieLens'

X_recipes = 10
X_users = 10
file_path = 'food/resources/recipes_DB/recipes'+X_recipes.__str__()+'_users'+X_users.__str__()+'_DB.csv'
ratings_df = pd.read_csv(file_path)
reader = Reader(rating_scale=(0, 5))
data_BBCGoodFood = Dataset.load_from_df(ratings_df[['user', 'item', 'rating']], reader)

data_MovieLens = Dataset.load_builtin('ml-100k')
file_path = 'food/resources/recipes_DB/u.csv'
ratings_movieLens_df = pd.read_csv(file_path, sep="\t")


datasets_dict = dict()
datasets_dict[BBCGoodFood_dataset_str] = data_BBCGoodFood
# datasets_dict[movieLens_dataset_str] = data_MovieLens


def optimize_memorybased_CF_algo(data):
    sim_options = {
        # "name": ["msd", "cosine", "pearson", "pearson_baseline"],
        "name": ["pearson"],
        "min_support": [3, 5],
        # "user_based": [False, True],
        "user_based": [True]
    }

    param_grid = {
        "k": [3, 6, 10, 15],
        "sim_options": sim_options
    }

    gs = GridSearchCV(KNNWithMeans, param_grid, measures=["rmse", "mae"], cv=3)
    gs.fit(data)

    print(gs.best_score["rmse"])
    print(gs.best_params["rmse"])

    print(gs.best_score["mae"])
    print(gs.best_params["mae"])

def optimize_modelbased_CF_algos(data):
    param_grid = {
        "n_factors": [1, 2, 3, 4],
        "n_epochs": [8, 9, 10, 11, 12],
        "lr_all": [0.02, 0.03, 0.04, 0.05],
        "reg_all": [0.05, 0.1, 0.2, 0.3]
    }
    gs = GridSearchCV(SVD, param_grid, measures=["rmse", "mae"], cv=3)

    gs.fit(data)

    print(gs.best_score["mae"])
    print(gs.best_params["mae"])

    print(gs.best_score["rmse"])
    print(gs.best_params["rmse"])



def compare_CF_algos():

    csv_res = list()
    csv_res.append(['', '', BBCGoodFood_dataset_str, '', '', '', '', movieLens_dataset_str, '', ''])
    csv_res.append(['Algo', 'Normalized MAE', 'Normalized RMSE', 'MAP@5', 'nDCG@5', 'Global score', 'Normalized MAE', 'Normalized RMSE', 'MAP@5', 'nDCG@5', 'Global score'])



    # Other algo and python libs
    # https://towardsdatascience.com/various-implementations-of-collaborative-filtering-100385c6dfe0

    kf = KFold(n_splits=5)

    algo_dict = dict()

    algo_dict['SVD-1-12-0.02-0.05-bestMAE'] = SVD(n_factors=1, n_epochs=12, lr_all=0.02, reg_all=0.05)
    algo_dict['SVD-3-8-0.02-0.3-bestRMSE'] = SVD(n_factors=2, n_epochs=11, lr_all=0.01, reg_all=0.2)

    algo_dict['NMF-21-2-bestMAE'] = NMF(n_factors=21, n_epochs=2)
    algo_dict['NMF-15-2-bestRMSE'] = NMF(n_factors=15, n_epochs=2)

    sim_options = {
        "name": "pearson",
        "min_support": 5,
        "user_based": True,  # Compute  similarities between items
    }
    algo_dict['User-b KNNwMeans'] = KNNWithMeans(k=10, sim_options=sim_options)

    # Item based performs poorly
    # sim_options = {
    #     "name": "cosine",
    #     "user_based": False,  # Compute  similarities between items
    # }
    # algo_dict['Item-b KNNwMeans'] = KNNWithMeans(sim_options=sim_options)

    scores_by_algo = dict()

    for i in range(0, 5):

        for algo_name, algo in algo_dict.items():

            print("Algo %s" % algo_name)

            res_row = list()
            res_row.append(algo_name)


            for dataset_name, data in datasets_dict.items():

                print("Dataset %s" % dataset_name)

                if dataset_name not in scores_by_algo.keys():
                    scores_by_algo[dataset_name] = list()

                sum_MAP = 0
                sum_nDCG = 0
                sum_RMSE = 0
                sum_MAE = 0
                all_pred = list()

                for trainset, testset in kf.split(data):
                    algo.fit(trainset)
                    predictions = algo.test(testset)
                    # print(predictions)

                    user_est_true = defaultdict(list)
                    for uid, _, true_r, est, _ in predictions:
                        user_est_true[uid].append((est, true_r))

                    precisions = dict()
                    recalls = dict()
                    five_or_more_pred = dict()
                    y_pred_list, y_true_list, y_pred_true_list = list(), list(), list()
                    for uid, ratings_pred in user_est_true.items():
                        if len(ratings_pred) > 4:
                            five_or_more_pred[uid] = ratings_pred
                            five_or_more_pred[uid] = list(reversed(sorted(five_or_more_pred[uid], key=lambda x: x[0])))
                            # five_or_more_pred[uid] = list(reversed(sorted(five_or_more_pred[uid], key=lambda x: x[1])))
                            # print(uid, five_or_more_pred[uid])
                            all_pred += [y for x,y in five_or_more_pred[uid]]
                            y_pred, y_true = list(), list()
                            new_five_or_more_pred_list = list()
                            for pred, true_val in five_or_more_pred[uid]:
                                rounded_pred = round(pred)
                                y_pred.append(rounded_pred)
                                y_true.append(true_val)
                            y_pred_list.append(y_pred)
                            y_true_list.append(y_true)
                            y_pred_true_list.append([y_pred, y_true])
                    # print(len(five_or_more_pred.keys()), len(y_pred_list))
                    map = MAPatK(y_pred_list, y_true_list, k=5)
                    nDCG = nDCGatK(y_true_list, k=5)
                    MAE = mean_absolute_error(flatten(y_true_list), flatten(y_pred_list))
                    RMSE = math.sqrt(mean_squared_error(flatten(y_true_list), flatten(y_pred_list)))
                    # print(map, nDCG, RMSE, MAE)
                    sum_MAP += map
                    sum_nDCG += nDCG
                    sum_MAE += MAE
                    sum_RMSE += RMSE

                normalized_RMSE = sum_RMSE/5
                normalized_RMSE = normalized_RMSE / 5 if dataset_name == BBCGoodFood_dataset_str else normalized_RMSE/5
                normalized_MAE = sum_MAE/5
                normalized_MAE = normalized_MAE / 5 if dataset_name == BBCGoodFood_dataset_str else normalized_MAE/5
                MAP = sum_MAP/5
                nDCG = sum_nDCG/5

                print("Normalized MAE = %.3f\nNormalized RMSE = %.3f\nMAP@5 = %.3f\nnDCG@5 = %.3f" % (normalized_MAE, normalized_MAE, MAP, nDCG))
                print("Mean of all predictions", stats.mean(all_pred))
                print("STD of all predictions", stats.stdev(all_pred))

                score = (normalized_RMSE + normalized_MAE + (1 - MAP) + (1 - nDCG)) / 4

                scores_by_algo[dataset_name].append([algo_name, score])

                for to_append in [normalized_MAE, normalized_RMSE, MAP, nDCG, score]:
                    res_row.append(to_append)

            csv_res.append(res_row)


        print("\n-------\n")
        print("Iteration", i)
        for dataset_name, scores in scores_by_algo.items():
            scores_by_algo[dataset_name] = list(sorted(scores_by_algo[dataset_name], key=lambda x: x[1]))
            print(scores_by_algo[dataset_name])


    with open('food/resources/recipes_DB/eval_CF.csv', 'w') as f:
        csvwriter = csv.writer(f)
        for row in csv_res:
            csvwriter.writerow(row)


def get_reco():

    best_recipes_for_all_users = dict()

    users = list(ratings_df['user'])
    users_unique = set(users)


    for i_u, u in enumerate(users_unique):

        if i_u < 100000:

            start = time.time()

            user_name = u
            # print(u)

            best_recipe = list()

            for i in range(0,10):
                # print('-----------')
                kf = KFold(n_splits=5)

                algo_name = 'SVD-1-12-0.02-0.05-bestMAE'
                algo = SVD(n_factors=1, n_epochs=12, lr_all=0.02, reg_all=0.05)

                # algo_name = 'SVD-3-8-0.02-0.3-bestRMSE'
                # algo = SVD(n_factors=2, n_epochs=11, lr_all=0.01, reg_all=0.)

                # algo_name = 'NMF-21-2-bestRMS'
                # algo = NMF(n_factors=21, n_epochs=2)

                # algo_name = 'NMF-15-2-bestRMSE'
                # algo = NMF(n_factors=15, n_epochs=2)

                # sim_options = {
                #     "name": "pearson",
                #     "min_support": 5,
                #     "user_based": True,  # Compute  similarities between items
                # }
                # algo_name = 'User-b KNNwMeans'
                # algo = KNNWithMeans(k=10, sim_options=sim_options)


                for trainset, testset in kf.split(data_BBCGoodFood):
                    algo.fit(trainset)

                #get a list of all recipes ids
                recipes_ids = ratings_df['item'].unique()
                recipes_rated_by_teresahall = ratings_df.loc[ratings_df['user'] == user_name, 'item']
                if i == 0:
                    ratings_df_2 = ratings_df.set_index('user', drop=False)
                    # print(ratings_df_2.loc[user_name, 'item':'rating'])
                # remove the recipes that teresahall has rated from the list of all recipe ids
                recipes_to_pred = np.setdiff1d(recipes_ids, recipes_rated_by_teresahall)

                # get predictions
                testset = [[user_name, item, 4.] for item in recipes_to_pred]
                predictions = algo.test(testset)
                random.shuffle(predictions)
                est_list = [pred.est for pred in predictions]
                # print(est_list)
                # print(stats.mean(est_list), stats.stdev(est_list), min(est_list), max(est_list), est_list.count(5))

                # get best prediction
                pred_ratings = np.array([pred.est for pred in predictions])
                pred_ratings_list = [[pred.iid, pred.est] for pred in predictions]
                pred_ratings_list_sorted = list(reversed(sorted(pred_ratings_list, key=lambda x: x[1])))

                for j in range(5):
                    recipe_id = pred_ratings_list_sorted[j][0]
                    best_recipe.append(recipe_id)

            best_recipes_count = list()
            # print("with", algo_name)
            # print("x = ", len(set(best_recipe)))
            for r in set(best_recipe):
                best_recipes_count.append([r, best_recipe.count(r)])

            best_recipes_count = list(reversed(sorted(best_recipes_count, key=lambda x: x[1])))

            print(time.time() - start)

            for x in best_recipes_count[:5]:
                r, n_reco = x[0][9:], x[1]
                # print(r, n_reco)
                if r not in best_recipes_for_all_users.keys():
                    best_recipes_for_all_users[r] = 0
                best_recipes_for_all_users[r] += n_reco

    best_recipes_for_all_users_list = list()
    for r, n_reco in best_recipes_for_all_users.items():
        best_recipes_for_all_users_list.append([r, n_reco])
    best_recipes_for_all_users_list = list(reversed(sorted(best_recipes_for_all_users_list, key=lambda x: x[1])))
    print("When recommending 5 recipes to each user of the DB, we recommend a total of %d different recipes" % len(best_recipes_for_all_users_list))
    for x in best_recipes_for_all_users_list:
        print(x[0], x[1])

if __name__ == "__main__":
    # optimize_memorybased_CF_algo(data_BBCGoodFood)
    # optimize_modelbased_CF_algos(data_BBCGoodFood)
    # compare_CF_algos()
    get_reco()
