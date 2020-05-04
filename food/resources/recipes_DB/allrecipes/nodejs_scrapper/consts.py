
X_users = 10
X_recipes = 10
json_reviews_file_path = 'food/resources/recipes_DB/allrecipes/nodejs_scrapper/reviews_all_recipes.json'
json_users_data_10_reviews = 'food/resources/recipes_DB/allrecipes/nodejs_scrapper/users_data_10reviews.json'
json_users_recipes_data_10reviews = 'food/resources/recipes_DB/allrecipes/nodejs_scrapper/users_recipes_data_10reviews.json'
json_xUsers_Xrecipes_path = 'food/resources/recipes_DB/allrecipes/nodejs_scrapper/DBu'+X_users.__str__()+'r'+X_recipes.__str__()+'.json'
csv_xUsers_Xrecipes_path = 'food/resources/recipes_DB/allrecipes/nodejs_scrapper/DBu'+X_users.__str__()+'r'+X_recipes.__str__()+'.csv'
csv_xUsers_Xrecipes_binary_path = 'food/resources/recipes_DB/allrecipes/nodejs_scrapper/DBu'+X_users.__str__()+'r'+X_recipes.__str__()+'_binary.csv'

svd_n_factors, svd_n_epochs, svd_lr_all, svd_reg_all = 5, 10, 0.006, 0.01
svd_best_RMSE_name = 'SVD-5-10-0.006-0.1-bestRMSE'
