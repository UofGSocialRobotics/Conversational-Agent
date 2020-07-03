# Paper to cite: http://yifanhu.net/PUB/cf.pdf
# https://www.ethanrosenthal.com/2016/10/19/implicit-mf-part-1/
# https://towardsdatascience.com/building-a-collaborative-filtering-recommender-system-with-clickstream-data-dffc86c8c65
# https://nbviewer.jupyter.org/github/jmsteinw/Notebooks/blob/master/RecEngine_NB.ipynb
# https://towardsdatascience.com/understanding-auc-roc-curve-68b2303cc9c5
# https://nbviewer.jupyter.org/github/jmsteinw/Notebooks/blob/master/RecEngine_NB.ipynb

import pandas as pd
import numpy as np
import scipy.sparse as sparse
import implicit
import random
import operator
import json
import csv
import statistics

from sklearn import metrics
from sklearn.preprocessing import MinMaxScaler

import food.resources.recipes_DB.allrecipes.nodejs_scrapper.consts as consts
import helper_functions as helper
import food.RS_utils as rs_utils
from ca_logging import log
from food.resources.data_collection.healthRecSys.json_to_csv import get_avg_healthScore



def make_train(ratings, pct_test = 0.2):
    '''
    This function will take in the original user-item matrix and "mask" a percentage of the original ratings where a
    user-item interaction has taken place for use as a test set. The test set will contain all of the original ratings,
    while the training set replaces the specified percentage of them with a zero in the original ratings matrix.

    parameters:

    ratings - the original ratings matrix from which you want to generate a train/test set. Test is just a complete
    copy of the original set. This is in the form of a sparse csr_matrix.

    pct_test - The percentage of user-item interactions where an interaction took place that you want to mask in the
    training set for later comparison to the test set, which contains all of the original ratings.

    returns:

    training_set - The altered version of the original data with a certain percentage of the user-item pairs
    that originally had interaction set back to zero.

    test_set - A copy of the original ratings matrix, unaltered, so it can be used to see how the rank order
    compares with the actual interactions.

    user_inds - From the randomly selected user-item indices, which user rows were altered in the training data.
    This will be necessary later when evaluating the performance via AUC.
    '''
    test_set = ratings.copy() # Make a copy of the original set to be the test set.
    test_set[test_set != 0] = 1 # Store the test set as a binary preference matrix
    training_set = ratings.copy() # Make a copy of the original data we can alter as our training set.
    nonzero_inds = training_set.nonzero() # Find the indices in the ratings data where an interaction exists
    nonzero_pairs = list(zip(nonzero_inds[0], nonzero_inds[1])) # Zip these pairs together of user,item index into list
    random.seed(0) # Set the random seed to zero for reproducibility
    num_samples = int(np.ceil(pct_test*len(nonzero_pairs))) # Round the number of samples needed to the nearest integer
    samples = random.sample(nonzero_pairs, num_samples) # Sample a random number of user-item pairs without replacement
    user_inds = [index[0] for index in samples] # Get the user row indices
    item_inds = [index[1] for index in samples] # Get the item column indices
    training_set[user_inds, item_inds] = 0 # Assign all of the randomly chosen user-item pairs to zero
    training_set.eliminate_zeros() # Get rid of zeros in sparse array storage after update to save space
    return training_set, test_set, list(set(user_inds)) # Output the unique list of user rows that were altered



def auc_score(predictions, test):
    '''
    This simple function will output the area under the curve using sklearn's metrics.

    parameters:

    - predictions: your prediction output

    - test: the actual target result you are comparing to

    returns:

    - AUC (area under the Receiver Operating Characterisic curve)
    '''
    fpr, tpr, thresholds = metrics.roc_curve(test, predictions)
    return metrics.auc(fpr, tpr)


def calc_mean_auc(training_set, altered_users, predictions, test_set):
    '''
    This function will calculate the mean AUC by user for any user that had their user-item matrix altered.

    parameters:

    training_set - The training set resulting from make_train, where a certain percentage of the original
    user/item interactions are reset to zero to hide them from the model

    predictions - The matrix of your predicted ratings for each user/item pair as output from the implicit MF.
    These should be stored in a list, with user vectors as item zero and item vectors as item one.

    altered_users - The indices of the users where at least one user/item pair was altered from make_train function

    test_set - The test set constucted earlier from make_train function



    returns:

    The mean AUC (area under the Receiver Operator Characteristic curve) of the test set only on user-item interactions
    there were originally zero to test ranking ability in addition to the most popular items as a benchmark.
    '''


    store_auc = [] # An empty list to store the AUC for each user that had an item removed from the training set
    popularity_auc = [] # To store popular AUC scores
    pop_items = np.array(test_set.sum(axis = 0)).reshape(-1) # Get sum of item iteractions to find most popular
    item_vecs = predictions[1]
    for user in altered_users: # Iterate through each user that had an item altered
        training_row = training_set[user,:].toarray().reshape(-1) # Get the training set row
        zero_inds = np.where(training_row == 0) # Find where the interaction had not yet occurred
        # Get the predicted values based on our user/item vectors
        user_vec = predictions[0][user,:]
        pred = user_vec.dot(item_vecs).toarray()[0,zero_inds].reshape(-1)
        # Get only the items that were originally zero
        # Select all ratings from the MF prediction for this user that originally had no iteraction
        actual = test_set[user,:].toarray()[0,zero_inds].reshape(-1)
        # Select the binarized yes/no interaction pairs from the original full data
        # that align with the same pairs in training
        pop = pop_items[zero_inds] # Get the item popularity for our chosen items
        store_auc.append(auc_score(pred, actual)) # Calculate AUC for the given user and store
        popularity_auc.append(auc_score(pop, actual)) # Calculate AUC using most popular and score
    # End users iteration

    return float('%.5f'%np.mean(store_auc)), float('%.5f'%np.mean(popularity_auc))
   # Return the mean AUC rounded to three decimal places for both test and popularity benchmark


def rec_items(customer_id, mf_train, user_vecs, item_vecs, customer_list, item_list, num_items=10):
    '''
    This function will return the top recommended items to our users

    parameters:

    customer_id - Input the customer's id number that you want to get recommendations for

    mf_train - The training matrix you used for matrix factorization fitting

    user_vecs - the user vectors from your fitted matrix factorization

    item_vecs - the item vectors from your fitted matrix factorization

    customer_list - an array of the customer's ID numbers that make up the rows of your ratings matrix
                    (in order of matrix)

    item_list - an array of the products that make up the columns of your ratings matrix
                    (in order of matrix)

    num_items - The number of items you want to recommend in order of best recommendations. Default is 10.

    returns:

    - The top n recommendations chosen based on the user/item vectors for items never interacted with/purchased
    '''

    cust_ind = np.where(customer_list == customer_id)[0][0] # Returns the index row of our customer id
    pref_vec = mf_train[cust_ind,:].toarray() # Get the ratings from the training set ratings matrix
    pref_vec = pref_vec.reshape(-1) + 1 # Add 1 to everything, so that items not purchased yet become equal to 1
    pref_vec[pref_vec > 1] = 0 # Make everything already purchased zero
    rec_vector = user_vecs[cust_ind,:].dot(item_vecs.T) # Get dot product of user vector and all item vectors
    # Scale this recommendation vector between 0 and 1
    min_max = MinMaxScaler()
    rec_vector_scaled = min_max.fit_transform(rec_vector.reshape(-1,1))[:,0]
    recommend_vector = pref_vec*rec_vector_scaled
    # Items already purchased have their recommendation multiplied by zero
    product_idx = np.argsort(recommend_vector)[::-1][:num_items] # Sort the indices of the items into order
    # of best recommendations
    rec_list = [] # start empty list to store items
    for index in product_idx:
        code = item_list[index]
        # rec_list.append([code, item_lookup.Description.loc[item_lookup.StockCode == code].iloc[0]])
        rec_list.append(code)
        # Append our descriptions to the list
    return rec_list

def fit_and_get_AUC(model, train_set, test_set, recipes_users_altered_test, alpha, params):
    model.fit((train_set*alpha).astype('double'))
    s = calc_mean_auc(train_set, recipes_users_altered_test, [sparse.csr_matrix(model.item_factors), sparse.csr_matrix(model.user_factors.T)], test_set)
    return s[0]

def grid_search(train_set, cv_set, recipes_users_altered_cv, alpha_values=[2], n_factors_values=[2], reg_values=[0.5, 0.6, 0.7], n_epochs_values=[35, 40, 50, 60], lr_values=[0.7, 0.8, 0.9, 1], iterations=5):
    scores = list()
    for alpha in alpha_values:
        for factors in n_factors_values:
            for reg in reg_values:
                for epochs in n_epochs_values:
                    if consts.algo_str == consts.algo_als:
                        AUCs_list = list()
                        for i in range(iterations):
                            model = implicit.als.AlternatingLeastSquares(factors=factors, regularization=reg, iterations=epochs)
                            params = (alpha, factors, reg, epochs)

                            AUC = fit_and_get_AUC(model, train_set, cv_set, recipes_users_altered_cv, alpha, params)
                            AUCs_list.append(AUC)
                        avg_AUC = statistics.mean(AUCs_list)
                        scores.append([params, avg_AUC])
                    elif consts.algo_str == consts.algo_bpr:
                        for lr in lr_values:
                            AUCs_list = list()
                            for i in range(iterations):
                                model = implicit.bpr.BayesianPersonalizedRanking(factors=factors, learning_rate=lr, regularization=reg, iterations=epochs)
                                params = (alpha, factors, lr, reg, epochs)
                                AUC = fit_and_get_AUC(model, train_set, cv_set, recipes_users_altered_cv, alpha, params)
                                AUCs_list.append(AUC)
                            avg_AUC = statistics.mean(AUCs_list)
                            scores.append([params, avg_AUC])
                    elif consts.algo_str == consts.algo_lmf:
                        for lr in lr_values:
                            AUCs_list = list()
                            for i in range(iterations):
                                model = implicit.lmf.LogisticMatrixFactorization(factors=factors, learning_rate=lr, regularization=reg, iterations=epochs)
                                params = (alpha, factors, lr, reg, epochs)
                                AUC = fit_and_get_AUC(model, train_set, cv_set, recipes_users_altered_cv, alpha, params)
                                AUCs_list.append(AUC)
                            avg_AUC = statistics.mean(AUCs_list)
                            scores.append([params, avg_AUC])

    scores = sorted(scores, key=operator.itemgetter(-1), reverse=True)
    print("\nBest parameters:")
    for i, e in enumerate(scores):
        print(e)
        if i > 20:
            break

def get_recipes_rated(user_id, mf_train, users, products_list):
    '''
    This just tells me which items have been already purchased by a specific user in the training set. 
    
    parameters: 
    
    customer_id - Input the customer's id number that you want to see prior purchases of at least once
    
    mf_train - The initial ratings training set used (without weights applied)
    
    customers_list - The array of customers used in the ratings matrix
    
    products_list - The array of products used in the ratings matrix
    
    returns:
    
    A list of item IDs and item descriptions for a particular customer that were already purchased in the training set
    '''
    cust_ind = np.where(users == user_id)[0][0] # Returns the index row of our customer id
    purchased_ind = mf_train[cust_ind, :].nonzero()[1] # Get column indices of purchased items
    recipes = products_list[purchased_ind] # Get the stock codes for our purchased items
    return recipes


def get_recipes_rated_from_json(user_id):
    with open(consts.json_xUsers_Xrecipes_path, 'r') as fjson:
        json_data = json.load(fjson)
    user_data = json_data['users_data']
    res = user_data[user_id]['recipes_commented']
    print(len(set(res)), user_data[user_id]['n_comments'])
    return res


def get_df_from_ratings_list(uid, ratings_list):
    new_df = pd.DataFrame({"item": [i for (i, _) in ratings_list], "user": [uid] * len(ratings_list), "rating": [r for (_, r) in ratings_list]})
    return new_df


############################################################################################
##                                            MAIN                                        ##
############################################################################################


def tune_hyperparam():
    print("\n----------------------------------\n")
    print("ALGO: ", consts.algo_str)
    print("\n==================================\n")
    item_user_sparse, user_item_sparse, users_arr, items_arr, train_set, cv_set, test_set, recipes_users_altered_cv, recipes_users_altered_test = prep(df, cv_bool=True)
    grid_search(train_set, cv_set, recipes_users_altered_cv)


def get_AUC_tuned_param():
    item_user_sparse, user_item_sparse, users_arr, items_arr, train_set, _, test_set, _, recipes_users_altered_test = prep(df)
    if consts.algo_str == consts.algo_als:
        model = implicit.als.AlternatingLeastSquares(factors=consts.factors, regularization=consts.reg, iterations=consts.epochs)
        print("Alpha, factors, reg, iterations:", consts.alpha, consts.factors, consts.reg, consts.epochs)
    elif consts.algo_str == consts.algo_bpr:
        model = implicit.bpr.BayesianPersonalizedRanking(factors=consts.factors, learning_rate=consts.lr, regularization=consts.reg, iterations=consts.epochs)
        print("Alpha, factors, lr, reg, iterations:", consts.alpha, consts.factors, consts.lr, consts.reg, consts.epochs)
    elif consts.algo_str == consts.algo_lmf:
        model = implicit.lmf.LogisticMatrixFactorization(factors=consts.factors, learning_rate=consts.lr, regularization=consts.reg, iterations=consts.epochs)
        print("Alpha, factors, lr, reg, iterations:", consts.alpha, consts.factors, consts.lr, consts.reg, consts.epochs)
    model.fit((train_set*consts.alpha).astype('double'))
    s = calc_mean_auc(train_set, recipes_users_altered_test, [sparse.csr_matrix(model.item_factors), sparse.csr_matrix(model.user_factors.T)], test_set)
    print("AUC:", s)
    return s


def prep(df, split_bool=True, cv_bool=False, pct_test=0.2, pct_cv=0.15):
    # Get unique customers / recipes and all quantities
    users = list(df['user'].unique())
    users_arr = np.array(users)
    items = list(df['item'].unique())
    items_arr = np.array(items)
    quantity = list(df['rating'])

    # Get the associated row / col indices
    df_users = df['user'].astype('category', categories=users).cat.codes
    df_items = df['item'].astype('category', categories=items).cat.codes
    # Build sparse matrix
    item_user_sparse = sparse.csr_matrix((quantity, (df_items, df_users)), shape=(len(items), len(users)))
    user_item_sparse = item_user_sparse.T.tocsr()

    # matrix_size = item_user_sparse.shape[0]*item_user_sparse.shape[1]
    # num_ratings = len(item_user_sparse.nonzero()[0])
    # sparcity = 100 * (1 - num_ratings/matrix_size)
    # print("Sparcity:", sparcity)
    if split_bool:

        train_set, test_set, recipes_users_altered_test = make_train(item_user_sparse, pct_test=pct_test)
        if cv_bool:
            train_set, cv_set, recipes_users_altered_cv = make_train(train_set, pct_test=pct_cv)
        else:
            cv_set, recipes_users_altered_cv = None, None

    else:
        train_set, cv_set, test_set, recipes_users_altered_cv, recipes_users_altered_test = None, None, None, None, None

    return item_user_sparse, user_item_sparse, users_arr, items_arr, train_set, cv_set, test_set, recipes_users_altered_cv, recipes_users_altered_test


def get_reco(df, uid, healthy_bias=False, recipes_data=None, n_recipes_torecommend=10, least_preferred=False, verbose=False):
    if healthy_bias and not recipes_data:
        raise AttributeError("If healthy_bias is True, must send recipes_data!")

    ###############################################################################
    ##              Should we train on trainset or on entire dataset?
    ###############################################################################
    item_user_sparse, user_item_sparse, users_arr, items_arr, _, _, _, _, _ = prep(df, split_bool=False)

    if consts.algo_str == consts.algo_als:
        model = implicit.als.AlternatingLeastSquares(factors=consts.factors, regularization=consts.reg, iterations=consts.epochs)
    else:
        print(consts.algo_str)
    model.fit((item_user_sparse*consts.alpha).astype('double'), show_progress=False)

    if healthy_bias or least_preferred:
        n_recipes_rated = df[df.user == uid].shape[0]
        N = len(items_arr) - n_recipes_rated
    else:
        N = n_recipes_torecommend

    cust_ind = np.where(users_arr == uid)[0][0]
    recommendations = model.recommend(cust_ind, user_item_sparse, N=N)

    # Get rid from rid-numeric
    reco = list()

    if not least_preferred: #normal reco
        for (ridx, v) in recommendations:
            reco.append([ridx, items_arr[ridx], v])
    else:
        recommendations.reverse()
        count = 0
        for (ridx, v) in recommendations:
            reco.append([ridx, items_arr[ridx], v])
            count += 1
            if count == n_recipes_torecommend:
                break

    # If healthy_bias, get final value reco
    if healthy_bias:
        to_scale = [score for (_, _, score) in reco]
        ids = [(nrid, rid) for (nrid, rid, _) in reco]
        scaled = helper.norm_vector(to_scale)

        FSAscores = [recipes_data[rid]["FSAscore"] for (_, rid) in ids]
        FSAscores_scaled = helper.norm_vector(FSAscores)

        reco_biased = list()
        for i, (nrid, rid) in enumerate(ids):
            pref_score, health_score = scaled[i], FSAscores_scaled[i]
            score = float(float(consts.coef_pref) * pref_score + float(consts.coef_healthy) * (1 - health_score)) / float(consts.coef_pref + consts.coef_healthy)
            reco_biased.append([nrid, rid, score, pref_score, 1-health_score])

        if not least_preferred: #normal reco
            reco_biased = sorted(reco_biased, key=operator.itemgetter(2), reverse=True)
        else:
            reco_biased = sorted(reco_biased, key=operator.itemgetter(2), reverse=False)
        # print(reco_biased)
        # print(n_recipes_torecommend)

        reco_biased = reco_biased[:n_recipes_torecommend]


        reco = reco_biased

    if verbose:
        count = 0
        for X in reco:
            if count < 10:
                print(X)
            else:
                print("%d more recommendations (%d total)" % (N - 10, N))
                break
            count += 1

    return reco


def get_reco_new_user(df, uid, ratings_list, healthy_bias=False, recipes_data=None, n_recipes_torecommend=10, least_preferred=False, verbose=False):

    df_new_user = get_df_from_ratings_list(uid, ratings_list)
    df = df.append(df_new_user)

    return get_reco(df, uid, healthy_bias=healthy_bias, recipes_data=recipes_data, n_recipes_torecommend=n_recipes_torecommend, least_preferred=least_preferred, verbose=verbose)



def get_coverage(healthy_bias=False, n_recipes_profile=10, n_recipes_torecommend=10):

    all_reco_dict = dict()

    with open(consts.json_xUsers_Xrecipes_path, 'r') as fjson:
        content = json.load(fjson)
    users_data = content['users_data']
    recipes_data = content['recipes_data']

    ratings_by_users = dict()
    for rid, rdata in recipes_data.items():
        for review in rdata['reviews']:
            uid = review['id']
            if uid not in ratings_by_users.keys():
                ratings_by_users[uid] = dict()
            rating = int(review['rating'])
            ratings_by_users[uid][rid] = rating
    print("Built ratings_by_users dictionary")

    for uid, udata in users_data.items():
        recipes_cooked = [[rid, rating] for rid, rating in ratings_by_users[uid].items()]
        ratings_new_user = random.sample(recipes_cooked, n_recipes_profile)
        # print(ratings_new_user)
        rec_list = get_reco_new_user(df, "new_user", ratings_new_user, healthy_bias=healthy_bias, recipes_data=recipes_data, n_recipes_torecommend=n_recipes_torecommend)
        for reco in rec_list:
            rid = reco[1]
            if rid not in all_reco_dict:
                all_reco_dict[rid] = 0
            all_reco_dict[rid] += 1
        # break

    all_reco_list = [(key, value) for key, value in all_reco_dict.items()]
    all_reco_list = sorted(all_reco_list, key=operator.itemgetter(1), reverse=True)

    total_recipes_recommended = len(all_reco_list)

    print("%d recipes recommended to %d users (with user profile of %d recipes)" % (total_recipes_recommended, len(users_data.keys()), n_recipes_profile))
    print("--> Coverage: %d / %d = %.2f%%" % (total_recipes_recommended, len(recipes_data.keys()), 100 * float(total_recipes_recommended) / len(recipes_data.keys())))

    for key, value in all_reco_list:
        print(key, value)

    with open(consts.csv_coverageHybrid, 'w') as csvf:
        print("writing to", consts.csv_coverageHybrid)
        csv_writer = csv.writer(csvf)
        for row in all_reco_list:
            csv_writer.writerow(row)


class ImplicitCFRS:


    def __init__(self):
        ImplicitCFRS.__instance = self
        self.healthy_bias = None

        self.n_algos = rs_utils.n_alogs
        self.algo_list = list()


        with open(consts.json_xUsers_Xrecipes_path, 'r') as f:
            content = json.load(f)
        self.recipes_data = content['recipes_data']

        self.df = pd.read_csv(consts.csv_xUsers_Xrecipes_path)

    def set_healthy_bias(self, healthy_bias):
        self.healthy_bias = healthy_bias


    def start(self):
        if self.healthy_bias == None:
            log.error("Must set a value for healthy_bias")
            raise ValueError("Healthy bias not set!")
        else:
            log.info("ImplicitCFRS: ready, healthy bias is %s" % self.healthy_bias.__str__())

    def get_coverage(self):
        return get_coverage(healthy_bias=self.healthy_bias)

    def get_reco(self, user_name, ratings_list, n_reco=10, verbose=False):
        return get_reco_new_user(self.df, user_name, ratings_list, healthy_bias=self.healthy_bias, recipes_data=self.recipes_data, n_recipes_torecommend=n_reco, verbose=verbose)

    def get_reco_least_preferred(self, user_name, ratings_list, n_reco=10, verbose=False):
        return get_reco_new_user(self.df, user_name, ratings_list, healthy_bias=self.healthy_bias, recipes_data=self.recipes_data, n_recipes_torecommend=n_reco, least_preferred=True, verbose=verbose)



if __name__ == "__main__":
    df = pd.read_csv(consts.csv_xUsers_Xrecipes_path)
    print(df.head())

    with open(consts.json_xUsers_Xrecipes_path, 'r') as f:
        content = json.load(f)
    recipes_data = content['recipes_data']

    # --- Tune hyperparameters
    # tune_hyperparam()
    # Get best AUC (with tuned params) over 100 iterations
    # AUC_list = list()
    # most_pop_AUC = None
    # for i in range(100):
    #     print(i)
    #     scores = get_AUC_tuned_param()
    #     AUC_list.append(scores[0])
    #     most_pop_AUC = scores[1]
    # print(statistics.mean(AUC_list))


    # --- Get recommendations
    # uid = '/cook/939980/'
    uid = random.choice(list(content['users_data'].keys()))
    reco = get_reco(df, uid, healthy_bias=True, recipes_data=recipes_data, verbose=True)
    reco = [x[1] for x in reco]
    print(get_avg_healthScore(reco))
    print("\n-----------------\n")
    reco = get_reco_least_recommended_recipes(df, uid, healthy_bias=True, recipes_data=recipes_data, verbose=True)
    reco = [x[1] for x in reco]
    print(reco)
    print(get_avg_healthScore(reco))
    #
    # print("\n-----------------\n")
    #
    # reco = get_reco(df, uid, healthy_bias=True, recipes_data=recipes_data, verbose=False)
    # reco = [x[1] for x in reco]
    # print(reco)
    # print(get_avg_healthScore(reco))

    # Test get reco for new user
    # uid = "lucile"
    # df = pd.read_csv(consts.csv_xUsers_Xrecipes_path)
    # ratings = [(rid, 5) for rid in rs_utils.get_recipes(df, "chicken")] + [(rid, 5) for rid in rs_utils.get_recipes(df, "chocolate")]
    # rs = ImplicitCFRS()
    # rs.set_healthy_bias(healthy_bias=True)
    # rs.start()
    # print(rs.get_reco(uid, ratings))
    # get_reco_new_user(df, uid, ratings, healthy_bias=True, recipes_data=recipes_data, verbose=True)

    # --- Get coverage
    # get_coverage(healthy_bias=True)

