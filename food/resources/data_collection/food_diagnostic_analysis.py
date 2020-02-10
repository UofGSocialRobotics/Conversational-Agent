import pandas
from collections import Counter
import matplotlib.pyplot as plt
import numpy as np
import json
import csv
import helper_functions as helper

def get_density(x_list, y_list):
    c = Counter(zip(x_list,y_list))
    s = [5*c[(xx,yy)] for xx,yy in zip(x_list,y_list)]
    return s

def generate_plots_with_demographics():

    df = pandas.read_csv("food/resources/sigir/food_states_all_sigir.csv")
    male_df = df.query("gender == 'male'")
    female_df = df.query("gender == 'female'")
    uk_df = df.query("living_in_UK != 'not_in_UK'")
    not_uk_df = df.query("living_in_UK == 'not_in_UK'")
    high_intention_to_cook_df = df.query("intention_to_cook >= 3.58")
    low_intention_to_cook_df = df.query("intention_to_cook < 3.58")

    healthiness_values_list = df['Healthiness'].to_list()
    fillingness_values_list = df['fillingness'].to_list()
    male_healthiness_values_list = male_df['Healthiness'].to_list()
    male_fillingness_values_list = male_df['fillingness'].to_list()
    female_healthiness_values_list = female_df['Healthiness'].to_list()
    female_fillingness_values_list = female_df['fillingness'].to_list()
    uk_healthiness_values_list = uk_df["Healthiness"].to_list()
    uk_fillingness_values_list = uk_df['fillingness'].to_list()
    not_uk_healthiness_values_list = not_uk_df["Healthiness"].to_list()
    not_uk_fillingness_values_list = not_uk_df['fillingness'].to_list()
    high_itc_healthiness_values_list = high_intention_to_cook_df["Healthiness"].to_list()
    high_itc_fillingness_values_list = high_intention_to_cook_df['fillingness'].to_list()
    low_itc_healthiness_values_list = low_intention_to_cook_df["Healthiness"].to_list()
    low_itc_fillingness_values_list = low_intention_to_cook_df['fillingness'].to_list()



    # print(healthiness_values_list)
    # print(fillingness_values_list)
    #
    # for i in range(len(healthiness_values_list)):
    #     print(healthiness_values_list[i], fillingness_values_list[i])

    density = get_density(healthiness_values_list, healthiness_values_list)
    male_denstiy = get_density(male_healthiness_values_list, male_fillingness_values_list)
    female_density = get_density(female_healthiness_values_list, female_fillingness_values_list)
    uk_density = get_density(uk_healthiness_values_list, uk_fillingness_values_list)
    not_uk_density = get_density(not_uk_healthiness_values_list, not_uk_fillingness_values_list)
    high_itc_density = get_density(high_itc_healthiness_values_list, high_itc_fillingness_values_list)
    low_itc_density = get_density(low_itc_healthiness_values_list, low_itc_fillingness_values_list)

    # density = [d*5 for d in density]
    fig, axs = plt.subplots(2, 2, sharex=True, sharey=True)

    axs[0,0].scatter(healthiness_values_list, fillingness_values_list, s=[d/5 for d in density])
    # coef = np.polyfit(healthiness_values_list, fillingness_values_list, 1)
    # poly1d_fn = np.poly1d(coef)
    # axs[0,0].plot(healthiness_values_list, poly1d_fn(healthiness_values_list), "--k")
    axs[0,0].set_title("All") #Food habits: healthiness and fillingness
    axs[0,1].scatter(not_uk_healthiness_values_list, not_uk_fillingness_values_list, s=not_uk_density, label="Not in UK")
    axs[0,1].scatter(uk_healthiness_values_list, uk_fillingness_values_list, s=uk_density, label="In UK")
    axs[0,1].legend(loc="upper right", fontsize=6)
    axs[0,1].set_title("UK vs non-UK people")
    axs[1,0].scatter(male_healthiness_values_list, male_fillingness_values_list, s=male_denstiy, label="Men")
    axs[1,0].scatter(female_healthiness_values_list, female_fillingness_values_list, s=female_density, label="Women")
    axs[1,0].set_title("Men vs women food habits")
    axs[1,0].legend(loc="upper right", fontsize=6)
    axs[1,1].scatter(high_itc_healthiness_values_list, high_itc_fillingness_values_list, s=high_itc_density, label="High itc")
    axs[1,1].scatter(low_itc_healthiness_values_list, low_itc_fillingness_values_list, s=low_itc_density, label="Low itc")
    axs[1,1].legend(loc="upper right", fontsize=6)
    axs[1,1].set_title("High vs low itc")
    # axs[1,1].scatter(female_healthiness_values_list, female_fillingness_values_list, s=female_density)
    # axs[1,1].set_title("Women food habits")

    for ax in axs.flat:
        ax.set(xlabel='Healthiness', ylabel='Fillingness')

    # Hide x labels and tick labels for top plots and y ticks for right plots.
    for ax in axs.flat:
        ax.label_outer()
    # plt.xlabel("Healthiness")
    # plt.ylabel("Fillingness")

    # plt.title("Food habits: healthiness and fillingness")
    plt.show()

D = 1

def generate_plot_trait_states():
    df = pandas.read_csv("food/resources/sigir/food_states_all_sigir.csv")
    df_foods = pandas.read_csv("food/resources/dm/food_model.csv")
    # df_foods = df_foods["healthiness", "food_fillingness"]
    df_snacks = df_foods.query("situation_name == 'Day time Snack' or situation_name == 'Evening Snack'")
    df_foods = df_foods.query("situation_name == 'Usual Dinner'")
    df_foods = helper.norm_pandas_matrix(df_foods)
    df_snacks = helper.norm_pandas_matrix(df_snacks)
    df_foods_meats = df_foods.query("food_type == 'meat'")
    df_foods_meals = df_foods.query("food_type == 'meal'")
    df_foods_sides = df_foods.query("food_type == 'side'")
    df_foods_desserts = df_foods.query("food_type == 'dessert'")
    # print(df_foods)


    healthiness_values_list = df['healthiness'].to_list()
    fillingness_values_list = df['fillingness'].to_list()
    density = get_density(healthiness_values_list, healthiness_values_list)

    h_meat_val_list = df_foods_meats['healthiness'].to_list()
    h_meal_val_list = df_foods_meals['healthiness'].to_list()
    h_side_val_list = df_foods_sides['healthiness'].to_list()
    h_dessert_val_list = df_foods_desserts['healthiness'].to_list()
    f_meat_val_list = df_foods_meats['food_fillingness'].to_list()
    f_meal_val_list = df_foods_meals['food_fillingness'].to_list()
    f_side_val_list = df_foods_sides['food_fillingness'].to_list()
    f_dessert_val_list = df_foods_desserts['food_fillingness'].to_list()

    h_snack_val_list = df_snacks['healthiness'].to_list()
    f_snack_val_list = df_snacks['food_fillingness'].to_list()

    trait_healthiness_values_list = df['Healthiness_trait'].to_list()
    trait_fillingness_values_list = df['fillingness_trait'].to_list()
    trait_density = get_density(trait_healthiness_values_list, trait_fillingness_values_list)
    state_healthiness_values_list = df['healthiness_state'].to_list()
    state_fillingness_values_list = df['fillingness_state'].to_list()
    state_density = get_density(state_healthiness_values_list, state_fillingness_values_list)

    db_foods_healthiness = df_foods["healthiness"].to_list()
    db_foods_fillingness = df_foods["food_fillingness"].to_list()
    db_foods_density = get_density(db_foods_healthiness,db_foods_fillingness)

    fig, axs = plt.subplots(2, 2, sharex=True, sharey=True)

    # axs[0,0].scatter(healthiness_values_list,fillingness_values_list, s=[d/D for d in density], label="people")
    axs[0,0].scatter(h_meat_val_list, f_meat_val_list, label="meats")
    axs[0,0].scatter(h_meat_val_list, f_meat_val_list, label="meats")
    axs[0,0].scatter(h_meal_val_list, f_meal_val_list, label="meals")
    axs[0,0].scatter(h_side_val_list, f_side_val_list, label="sides")
    # axs[0,0].scatter(h_dessert_val_list, f_dessert_val_list, label="desserts")
    # axs[0,0].scatter(h_snack_val_list, f_snack_val_list, label="snacks")
    axs[0,0].legend(loc="upper right", fontsize=6)
    axs[0,0].set_title("Foods")

    axs[0,1].scatter(trait_healthiness_values_list, trait_fillingness_values_list, s=[d/D for d in trait_density], label="trait")
    axs[0,1].scatter(state_healthiness_values_list, state_fillingness_values_list, s=[d/D for d in state_density], label="state")
    axs[0,1].legend(loc="upper right", fontsize=6)
    axs[0,1].set_title("Trait vs. state")


    for ax in axs.flat:
        ax.set(xlabel='Healthiness', ylabel='Fillingness')
    # Hide x labels and tick labels for top plots and y ticks for right plots.
    # for ax in axs.flat:
    #     ax.label_outer()
    plt.show()


def study_correlations_state_trait():
    df = pandas.read_csv("food/resources/sigir/food_states_all_sigir.csv")
    fig, axs = plt.subplots(1, 2, sharex=True, sharey=True)

    trait_healthiness_values_list = df['Healthiness_trait'].to_list()
    trait_fillingness_values_list = df['fillingness_trait'].to_list()
    state_healthiness_values_list = df['healthiness_state'].to_list()
    state_fillingness_values_list = df['fillingness_state'].to_list()
    h_density = get_density(trait_healthiness_values_list, state_healthiness_values_list)
    f_density = get_density(trait_fillingness_values_list, state_fillingness_values_list)

    axs[0].scatter(trait_healthiness_values_list, state_healthiness_values_list, s=h_density)
    axs[0].set_title("Healthiness: state and trait")
    axs[1].scatter(trait_fillingness_values_list, state_fillingness_values_list, s=f_density)
    axs[1].set_title("Fillingness: state and trait")
    for ax in axs.flat:
        ax.set(xlabel='Trait', ylabel='State')
    plt.show()



def convert_json_to_csv():
    with open("food/resources/data_collection/sigir/food_averages_all_sigir.csv", "w") as fcsv:
        csv_writer = csv.writer(fcsv)
        csv_writer.writerow(["healthiness","fillingness"])
        with open('food/resources/data_collection/sigir/food_averages_all_sigir.json', 'r') as fjson:
            content = json.load(fjson)
            for elt in content:
                healthiness_val = elt["healthiness"]
                if isinstance(healthiness_val, bool):
                    healthiness_val = 0.75 if healthiness_val else -0.75
                fillingness_val = elt["food_fillingness"]
                if isinstance(fillingness_val, bool):
                    fillingness_val = 0.75 if fillingness_val else -0.75
                csv_writer.writerow([healthiness_val, fillingness_val])


if __name__ == "__main__":
    convert_json_to_csv()
    # study_correlations_state_trait()
