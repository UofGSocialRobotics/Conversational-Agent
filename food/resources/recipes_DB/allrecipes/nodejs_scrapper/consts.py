BBCGoodFood = "BBDGoodFood"
Allrecipes = "allrecipes"

WEBSITE = Allrecipes

sparse_model = "sparse"
dense_model = "dense"
intermediate_model = "intermediate"

model = dense_model

algo_als = "als"
algo_bpr = "brp"
algo_lmf = "lmf"
algo_str = algo_als

coef_pref = 3
coef_healthy = 1

if WEBSITE == Allrecipes:

    reviews = "reviews"
    rating = "rating"
    uid = "id"

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
        if algo_str == algo_als:
            alpha = 2
            factors = 6
            reg = 0.07
            epochs = 27
        elif algo_str == algo_bpr:
            alpha = 13
            factors = 14
            lr = 0.04
            reg = 0.08
            epochs = 80
        elif algo_str == algo_lmf:
            alpha = 2
            factors = 2
            lr = 0.9
            reg = 0.6
            epochs = 60

    binary_bool = False

    json_fullDB_path = 'food/resources/recipes_DB/allrecipes/nodejs_scrapper/fullDB.json'
    json_reviews_file_path = 'food/resources/recipes_DB/allrecipes/nodejs_scrapper/reviews_all_recipes.json'

    json_users_data_10_reviews = 'food/resources/recipes_DB/allrecipes/nodejs_scrapper/users_data_10reviews.json'
    json_recipes_data_10reviews = 'food/resources/recipes_DB/allrecipes/nodejs_scrapper/recipes_data_10reviews.json'

    json_xUsers_Xrecipes_path = 'food/resources/recipes_DB/allrecipes/nodejs_scrapper/DBu'+X_users.__str__()+'r'+X_recipes.__str__()+'.json'
    json_rids_list_xUsers_Xrecipes_path = 'food/resources/recipes_DB/allrecipes/nodejs_scrapper/DBu'+X_users.__str__()+'r'+X_recipes.__str__()+'_ridsList.json'
    json_descriptions_xUsers_Xrecipes_path = 'food/resources/recipes_DB/allrecipes/nodejs_scrapper/recipes_descriptions_u'+X_users.__str__()+'r'+X_recipes.__str__()+'.json'
    json_failedTagging_xUsers_Xrecipes_path = 'food/resources/recipes_DB/allrecipes/nodejs_scrapper/failedTagging_u'+X_users.__str__()+'r'+X_recipes.__str__()+'.json'
    json_xUsers_Xrecipes_withDiets_path = 'food/resources/recipes_DB/allrecipes/nodejs_scrapper/DBu'+X_users.__str__()+'r'+X_recipes.__str__()+'_withDiets.json'

    csv_xUsers_Xrecipes_path = 'food/resources/recipes_DB/allrecipes/nodejs_scrapper/DBu'+X_users.__str__()+'r'+X_recipes.__str__()+'.csv'
    csv_xUsers_Xrecipes_binary_path = 'food/resources/recipes_DB/allrecipes/nodejs_scrapper/DBu'+X_users.__str__()+'r'+X_recipes.__str__()+'_binary.csv'

    txt_coverageHealth = 'food/resources/recipes_DB/allrecipes/nodejs_scrapper/coverageHealth_u'+X_users.__str__()+'r'+X_recipes.__str__()+'.txt'
    txt_coveragePref = 'food/resources/recipes_DB/allrecipes/nodejs_scrapper/coveragePref_u'+X_users.__str__()+'r'+X_recipes.__str__()+'.txt'
    txt_coverageHybrid = 'food/resources/recipes_DB/allrecipes/nodejs_scrapper/coverageHybrid_u'+X_users.__str__()+'r'+X_recipes.__str__()+'.txt'
    csv_coverageHybrid = 'food/resources/recipes_DB/allrecipes/nodejs_scrapper/coverageHybrid_u'+X_users.__str__()+'r'+X_recipes.__str__()+'.csv'

    svd_n_factors, svd_n_epochs, svd_lr_all, svd_reg_all = 5, 10, 0.006, 0.01
    svd_best_RMSE_name = 'SVD-5-10-0.006-0.1-bestRMSE'


elif WEBSITE == BBCGoodFood:

    reviews = "comments"
    rating = "n_stars"
    uid = "user_name"

    if model == dense_model:
        X_users = 5
        X_recipes = 5
        alpha = 10
        factors = 3
        reg = 0.01
        epochs = 50
    else:
        raise ValueError("Not impremented yet!")

    json_xUsers_Xrecipes_path = 'food/resources/recipes_DB/BBCGoodFood/recipes'+X_recipes.__str__()+'_users'+X_users.__str__()+'_DB.json'
    csv_xUsers_Xrecipes_path = 'food/resources/recipes_DB/BBCGoodFood/recipes'+X_recipes.__str__()+'_users'+X_users.__str__()+'_DB.csv'



