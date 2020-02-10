from food.recipe_content_based_ResSys import ContentBasedRecSys
import food.food_config as fc

def print_recipe_list(r_list):
    for r in r_list:
        print(r[fc.title])

if __name__ == "__main__":
    cbrs = ContentBasedRecSys()

    print("------ With celery")
    recipes_w_avocado = cbrs.get_recipes_with_ingredient("celery")
    print_recipe_list(recipes_w_avocado)

    print("------ Vegetarian")
    veg_recipes = cbrs.get_vegetarian_recipes()
    print_recipe_list(veg_recipes)

    print("------ Vegan")
    recipes = cbrs.get_vegan_recipes()
    print_recipe_list(recipes)

    print("------ GF")
    recipes = cbrs.get_glutenfree_recipes()
    print_recipe_list(recipes)

    print("------ Dairy free")
    recipes = cbrs.get_dairyfree_recipes()
    print_recipe_list(recipes)

    print("------ Healthy")
    recipes = cbrs.get_healthy_recipes()
    print_recipe_list(recipes)

    print("------ Ready in 10 min")
    recipes = cbrs.get_recipes_ready_in_time(10)
    print_recipe_list(recipes)

    print("------ With celery ready in 10 min")
    recipes = cbrs.get_recipes('celery', 10)
    print_recipe_list(recipes)

    print("------ With pasta")
    recipes_w_avocado = cbrs.get_recipes_with_ingredient("pasta")
    print_recipe_list(recipes_w_avocado)
