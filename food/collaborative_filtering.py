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
import json
import operator
import food.resources.recipes_DB.allrecipes.nodejs_scrapper.consts as consts

from ca_logging import log

from surprise import Dataset
from surprise import SVD, NMF
from surprise.model_selection import KFold
from surprise import KNNWithMeans
from surprise.model_selection import GridSearchCV
from surprise.prediction_algorithms.predictions import Prediction

from sklearn.metrics import mean_squared_error, mean_absolute_error

import food.RS_utils as rs_utils


flatten = lambda l: [item for sublist in l for item in sublist]



ratings_df = pd.read_csv(consts.csv_xUsers_Xrecipes_path)
reader = Reader(rating_scale=(1, 5))
data = Dataset.load_from_df(ratings_df[['user', 'item', 'rating']], reader)

datasets_dict = dict()
datasets_dict["allrecipes.com"] = data


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
        "n_factors": [3, 4, 5],
        "n_epochs": [7, 8, 9, 10],
        "lr_all": [0.004, 0.006, 0.008, 0.01],
        "reg_all": [0.006, 0.1, 0.2]
    }
    gs = GridSearchCV(SVD, param_grid, measures=["rmse", "mae"], cv=3)

    gs.fit(data)

    print(gs.best_score["mae"])
    print(gs.best_params["mae"])

    print(gs.best_score["rmse"])
    print(gs.best_params["rmse"])



def compare_CF_algos():

    csv_res = list()
    csv_res.append(['Algo', 'Normalized MAE', 'Normalized RMSE', 'MAP@5', 'nDCG@5', 'Global score'])



    # Other algo and python libs
    # https://towardsdatascience.com/various-implementations-of-collaborative-filtering-100385c6dfe0

    kf = KFold(n_splits=5)

    algo_dict = dict()

    # algo_dict['SVD-1-12-0.02-0.05-bestMAE'] = SVD(n_factors=1, n_epochs=12, lr_all=0.02, reg_all=0.05)
    algo_dict[consts.svd_best_RMSE_name] = SVD(n_factors=consts.svd_n_factors, n_epochs=consts.svd_n_epochs, lr_all=consts.svd_lr_all, reg_all=consts.svd_reg_all)

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
                normalized_MAE = sum_MAE/5
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


    # with open(eval_CF_path, 'w') as f:
    #     csvwriter = csv.writer(f)
    #     for row in csv_res:
    #         csvwriter.writerow(row)



def get_reco(algo_list, user_name, healthy_bias=False, ratings_list=list(), verbose=False):
    if verbose:
        print(user_name)

    with open(consts.json_xUsers_Xrecipes_path, 'r') as f:
        content = json.load(f)

    start = time.time()

    best_recipe = list()

    for algo in algo_list:

        idx = ratings_df.last_valid_index()
        for ratings_data in ratings_list:
            recipe_id, rating = ratings_data[0], ratings_data[1]
            idx += 1
            ratings_df.loc[idx] = [recipe_id, user_name, rating]

        #get a list of all recipes ids
        recipes_ids = ratings_df['item'].unique()
        recipes_rated_by_user = ratings_df.loc[ratings_df['user'] == user_name, 'item']
        # if i == 0:
        #     ratings_df_2 = ratings_df.set_index('user', drop=False)
        # remove the recipes that teresahall has rated from the list of all recipe ids
        recipes_to_pred = np.setdiff1d(recipes_ids, recipes_rated_by_user)

        # get predictions
        testset = [[user_name, item, 4.] for item in recipes_to_pred]
        predictions = algo.test(testset)
        random.shuffle(predictions)

        # get best prediction
        pred_ratings_list = [[pred.iid, pred.est] for pred in predictions]
        n_healthy = 0
        if healthy_bias:
            new_pred_ratings_list = list()
            for x in pred_ratings_list:
                rid, pred = x[0], x[1]
                h = rs_utils.FSA_heathsclore(content['recipes_data'][rid])
                # h_scaled = 1 - float(h-4)/8
                if h < 7:
                    h_scaled = 3
                elif h > 9:
                    h_scaled = 1
                else:
                    h_scaled = 2
                h_scaled = h_scaled / 3
                if h_scaled == 1:
                    n_healthy += 1
                pred_scaled = pred/5
                # print(pred_scaled, h_scaled)
                pred = (rs_utils.coef_pref*pred_scaled + rs_utils.coef_healthy*h_scaled) / (rs_utils.coef_pref + rs_utils.coef_healthy) * 5
                new_pred_ratings_list.append([rid, pred])
            # print(n_healthy, len(pred_ratings_list))
            pred_ratings_list = new_pred_ratings_list
        pred_ratings_list_sorted = list(reversed(sorted(pred_ratings_list, key=lambda x: x[1])))

        for j in range(5):
            recipe_id = pred_ratings_list_sorted[j][0]
            best_recipe.append(recipe_id)


        best_recipes_count = list()
        for r in set(best_recipe):
            best_recipes_count.append([r, best_recipe.count(r)])

        best_recipes_count = list(reversed(sorted(best_recipes_count, key=lambda x: x[1])))

    reco = [x[0] for x in best_recipes_count[:rs_utils.from_n_best]]
    if rs_utils.n_reco != rs_utils.from_n_best:
        random.shuffle(reco)
        reco = reco[:rs_utils.n_reco]

    if verbose:
        print(time.time() - start)
        for r in reco:
            print(r)

    return reco


def get_coverage(algo_list, healthy_bias=False, verbose=False):

    best_recipes_for_all_users = dict()

    users = list(ratings_df['user'])
    users_unique = set(users)

    recipes = list(ratings_df['item'])
    recipes_unique = set(recipes)
    total_recipes = len(recipes_unique)

    for i_u, u in enumerate(users_unique):

        if i_u < 100000:

            reco = get_reco(algo_list=algo_list, user_name=u, healthy_bias=healthy_bias, verbose=verbose)

            for r in reco:
                if r not in best_recipes_for_all_users.keys():
                    best_recipes_for_all_users[r] = 1
                else:
                    best_recipes_for_all_users[r] += 1

    n_recommended = len(best_recipes_for_all_users.keys())
    print("When recommending 5 recipes to each user of the DB, we recommend a total of %d (%.2f%%) different recipes" % (n_recommended, float(n_recommended)/total_recipes*100))
    sorted_best_recipes_for_all_users = sorted(best_recipes_for_all_users.items(), key=operator.itemgetter(1), reverse=True)
    # print(sorted_best_recipes_for_all_users)
    for x0, x1 in sorted_best_recipes_for_all_users:
        print(x0, x1, float(x1)/len(users_unique)*100)


class CFRS:
    """Singleton class"""
    __instance = None

    @staticmethod
    def getInstance():
        """
        :return: the unique ServerUsingFirebase object
        """
        if CFRS.__instance == None:
            CFRS()
        return CFRS.__instance


    def __init__(self, healthy_bias=False):
        if CFRS.__instance != None:
            log.debug("Calling constructor of CFRS")
        else:
            CFRS.__instance = self
            self.healthy_bias = healthy_bias

            self.n_algos = rs_utils.n_alogs
            self.algo_list = list()


    def start(self):
        log.info("Starting CFRS, training...")

        for i in range(self.n_algos):
            kf = KFold(n_splits=5)
            # algo = SVD(n_factors=consts.svd_n_epochs, n_epochs=consts.svd_n_epochs, lr_all=consts.svd_lr_all, reg_all=consts.svd_reg_all)
            algo = SVD()
            for trainset, testset in kf.split(data):
                algo.fit(trainset)

        self.algo_list.append(algo)

        log.info("Ready to start!!")


    def get_coverage(self):
        return get_coverage(algo_list=self.algo_list, healthy_bias=self.healthy_bias, verbose=False)


    def get_reco(self, user_name, ratings_list):
        return get_reco(self.algo_list, user_name, healthy_bias=self.healthy_bias, ratings_list=ratings_list, verbose=False)


def get_recipes(key_word, n=5):
    rids = ratings_df.item.unique().tolist()
    res = list()
    for r in rids:
        if key_word in r:
            res.append(r)
            if len(res) == n:
                return res
    return res

if __name__ == "__main__":
    # optimize algo
    # optimize_modelbased_CF_algos(data)

    # compare_CF_algos()

    ratings_list = [[rid, 5] for rid in get_recipes("chicken", 5)] + [[rid, 1] for rid in get_recipes("cake", 5)]
    print(ratings_list)

    cfrs = CFRS()
    cfrs.start()
    # cfrs.get_coverage()
    #



    # ratings_list = [
        # ['188473/buffalo-chicken-wraps/', 5]]
    user_name = 'lucile_uniqueID0101'
    print(cfrs.get_reco(user_name, ratings_list))
