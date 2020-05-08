import implicit

sparse_model = "sparse"
dense_model = "dense"
intermediate_model = "intermediate"

model = dense_model

algo_als = "als"
algo_bpr = "brp"

if model == sparse_model:
    X_users = 10
    X_recipes = 10
    alpha = 52
    factors = 4
    reg = 0.003
    epochs = 20
elif model == intermediate_model:
    X_users = 20
    X_recipes = 20
elif model == dense_model:
    X_users = 30
    X_recipes = 25
    alpha = 2
    factors = 6
    reg = 0.07
    epochs = 27
    algo_str = algo_bpr

binary_bool = False

json_reviews_file_path = 'food/resources/recipes_DB/allrecipes/nodejs_scrapper/reviews_all_recipes.json'
json_users_data_10_reviews = 'food/resources/recipes_DB/allrecipes/nodejs_scrapper/users_data_10reviews.json'
json_users_recipes_data_10reviews = 'food/resources/recipes_DB/allrecipes/nodejs_scrapper/users_recipes_data_10reviews.json'
json_xUsers_Xrecipes_path = 'food/resources/recipes_DB/allrecipes/nodejs_scrapper/DBu'+X_users.__str__()+'r'+X_recipes.__str__()+'.json'
csv_xUsers_Xrecipes_path = 'food/resources/recipes_DB/allrecipes/nodejs_scrapper/DBu'+X_users.__str__()+'r'+X_recipes.__str__()+'.csv'
csv_xUsers_Xrecipes_binary_path = 'food/resources/recipes_DB/allrecipes/nodejs_scrapper/DBu'+X_users.__str__()+'r'+X_recipes.__str__()+'_binary.csv'

svd_n_factors, svd_n_epochs, svd_lr_all, svd_reg_all = 5, 10, 0.006, 0.01
svd_best_RMSE_name = 'SVD-5-10-0.006-0.1-bestRMSE'
