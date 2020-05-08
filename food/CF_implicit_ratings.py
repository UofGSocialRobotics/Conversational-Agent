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

from sklearn import metrics
from sklearn.preprocessing import MinMaxScaler

import food.resources.recipes_DB.allrecipes.nodejs_scrapper.consts as consts
import food.RS_utils as rs_utils




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

def grid_search(train_set, cv_set, recipes_users_altered_cv, alpha_values=[5, 10, 40], n_factors_values=[3, 5, 7, 10], reg_values=[0.001, 0.01, 0.1], n_epochs_values=[15, 25, 35], lr_values=[0.001, 0.01, 0.1]):
    scores = list()
    for alpha in alpha_values:
        for factors in n_factors_values:
            for reg in reg_values:
                for epochs in n_epochs_values:
                    if consts.algo_str == consts.algo_als:
                        model = implicit.als.AlternatingLeastSquares(factors=factors, regularization=reg, iterations=epochs)
                        params = (alpha, factors, reg, epochs)
                        scores.append([params, fit_and_get_AUC(model, train_set, cv_set, recipes_users_altered_cv, alpha, params)])
                    elif consts.algo_str == consts.algo_bpr:
                        for lr in lr_values:
                            model = implicit.bpr.BayesianPersonalizedRanking(factors=factors, learning_rate=lr, regularization=reg, iterations=epochs)
                            params = (alpha, factors, lr, reg, epochs)
                            scores.append([params, fit_and_get_AUC(model, train_set, cv_set, recipes_users_altered_cv, alpha, params)])
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

df = pd.read_csv(consts.csv_xUsers_Xrecipes_path)
print(df.head())


def tune_hyperparam():
    item_user_sparse, user_item_sparse, users_arr, items_arr, train_set, cv_set, test_set, recipes_users_altered_cv, recipes_users_altered_test = prep(df, cv_bool=True)
    grid_search(train_set, cv_set, recipes_users_altered_cv)


def get_AUC_tuned_param():
    item_user_sparse, user_item_sparse, users_arr, items_arr, train_set, _, test_set, _, recipes_users_altered_test = prep(df)
    if consts.algo_str == consts.algo_als:
        model = implicit.als.AlternatingLeastSquares(factors=consts.factors, regularization=consts.reg, iterations=consts.epochs)
    model.fit((train_set*consts.alpha).astype('double'))
    s = calc_mean_auc(train_set, recipes_users_altered_test, [sparse.csr_matrix(model.item_factors), sparse.csr_matrix(model.user_factors.T)], test_set)
    print("Alpha, factors, reg, iterations:", consts.alpha, consts.factors, consts.reg, consts.epochs)
    print("AUC:", s)


def prep(df, cv_bool=False, pct_test=0.2, pct_cv=0.15):
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

    matrix_size = item_user_sparse.shape[0]*item_user_sparse.shape[1]
    num_ratings = len(item_user_sparse.nonzero()[0])
    sparcity = 100 * (1 - num_ratings/matrix_size)
    print("Sparcity:", sparcity)

    train_set, test_set, recipes_users_altered_test = make_train(item_user_sparse, pct_test=pct_test)
    if cv_bool:
        train_set, cv_set, recipes_users_altered_cv = make_train(train_set, pct_test=pct_cv)
    else:
        cv_set, recipes_users_altered_cv = None, None

    return item_user_sparse, user_item_sparse, users_arr, items_arr, train_set, cv_set, test_set, recipes_users_altered_cv, recipes_users_altered_test



def get_reco_new_user(df, uid, ratings_list):
    ###############################################################################
    ##              Should we train on trainset or on entire dataset?
    ###############################################################################

    df_new_user = get_df_from_ratings_list(uid, ratings_list)
    df = df.append(df_new_user)

    item_user_sparse, user_item_sparse, users_arr, items_arr, train_set, _, test_set, _, recipes_users_altered_test = prep(df)

    if consts.algo_str == consts.algo_als:
        model = implicit.als.AlternatingLeastSquares(factors=consts.factors, regularization=consts.reg, iterations=consts.epochs)
    model.fit((train_set*consts.alpha).astype('double'))

    cust_ind = np.where(users_arr == uid)[0][0]
    recommendations = model.recommend(cust_ind, user_item_sparse)
    #
    for (ridx, v) in recommendations:
        print(ridx, items_arr[ridx], v)


def get_coverage(n_recipes_profile):

    # Get unique customers / recipes and all quantities
    users = list(df['user'].unique())
    users_arr = np.array(users)
    recipes = list(df['item'].unique())
    recipes_arr = np.array(recipes)
    quantity = list(df['rating'])

    # Get the associated row / col indices
    rows = df['user'].astype('category', categories=users).cat.codes
    cols = df['item'].astype('category', categories=recipes).cat.codes
    # Build sparse matrix
    ratings_sparse = sparse.csr_matrix((quantity, (rows, cols)), shape=(len(users), len(recipes)))

    matrix_size = ratings_sparse.shape[0]*ratings_sparse.shape[1]
    num_ratings = len(ratings_sparse.nonzero()[0])
    sparcity = 100 * (1 - num_ratings/matrix_size)
    print("Sparcity:", sparcity)

    train_set, test_set, recipes_users_altered_test = make_train(ratings_sparse, pct_test=0.2)

    user_vecs, item_vecs = implicit.alternating_least_squares((train_set*consts.alpha).astype('double'), factors=consts.factors, regularization=consts.reg, iterations=consts.epochs)
    scores = calc_mean_auc(train_set, recipes_users_altered_test, [sparse.csr_matrix(user_vecs), sparse.csr_matrix(item_vecs.T)], test_set)
    print(scores)

    all_reco_dict = dict()

    for uid in users:
        # recipes_cooked = get_recipes_rated(uid, ratings_sparse, users_arr, recipes_arr)[:n_recipes_profile]
        rec_list = rec_items(uid, ratings_sparse, user_vecs, item_vecs, users_arr, recipes_arr, num_items=10)
        for rid in rec_list:
            if rid not in all_reco_dict:
                all_reco_dict[rid] = 0
            all_reco_dict[rid] += 1

    all_reco_list = [(key, value) for key, value in all_reco_dict.items()]
    all_reco_list = sorted(all_reco_list, key=operator.itemgetter(1), reverse=True)

    total_recipes_recommended = len(all_reco_list)

    print("%d recipes recommended to %d users (with user profile of %d recipes)" % (total_recipes_recommended, len(users), n_recipes_profile))
    print("--> Coverage: %d / %d = %.2f%%" % (total_recipes_recommended, len(recipes), 100 * float(total_recipes_recommended) / len(recipes)))



if __name__ == "__main__":
    # Tune hyperparameters
    tune_hyperparam()
    # get_AUC_tuned_param()

    # Test get reco for new user
    # uid = "lucile"
    # ratings = [(rid, 5) for rid in rs_utils.get_recipes(df, "chicken")] + [(rid, 5) for rid in rs_utils.get_recipes(df, "chocolate")]
    # get_reco_new_user(df, uid, ratings)
