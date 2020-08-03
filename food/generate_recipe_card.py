import json
import random
import urllib.request


import food.resources.recipes_DB.allrecipes.nodejs_scrapper.consts as consts

img_dir_path = 'food/resources/recipes_DB/allrecipes/images/'


html1 = """
<!DOCTYPE html>
<html>
    <link href="/Users/lucileca/Desktop/Conversational_Agent/client_side/chat.css" rel="stylesheet" id="bootstrap-css">
    <link href="/Users/lucileca/Desktop/Conversational_Agent/client_side/avatar.css" rel="stylesheet" id="error_css">

    <link href="/Users/lucileca/Desktop/Conversational_Agent/client_side/rs_eval.css" rel="stylesheet" id="rs-css">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/css/font-awesome.min.css">
    <center>
        <div class="recipe_grid">
            <div class="recipe_img"><img class="center-cropped-large"
                    src="/Users/lucileca/Desktop/Conversational_Agent/server_side/food/resources/img/recipe_img/
"""
# add picture
html2 = """
        "
                    id="recipe_img" height="250px"></div>
            <div class="recipe_title">
                <center><span id="recipe_title">
"""
# add title
html3 = """
                </span><br><br>
                </center>
            </div>
            <div class="recipe_rating" id="recipe_rating_id">
                <img
                    src="/Users/lucileca/Desktop/Conversational_Agent/server_side/food/resources/img/
"""
# add stars image
html4 = """
                    "
                    id="rstars_img" height="25px">
            </div>
            <div class="recipe_tag" id="recipe_tag_div"><img src="/Users/lucileca/Desktop/Conversational_Agent/client_side/img/
"""
# add health tag img
html5 = """
            "
                    width="150px" id="health_tag_img"></div>
            <div class="recipe_time"><b>Prep: 
"""
# add prep time
html6 = """
            </b>
                <span id="prep_time"> </span><br><br><b>Cook: 
"""
# add cook time
html7 = """
                </b>
                <span id="cook_time"> </span><br><br><b>Total: 
"""
# add total time
html8 = """
                </b>
                <span id="total_time"> </span></div>
            <div class="recipe_servings"><b>Servings:
"""
# add servings
html8_bis = """
                </b>
                <span id="servings"> </span></div>
            <div class="recipe_description" id="recipe_description">
"""
# add description
html8_ter = """
            </div>
            <div class="recipe_ingredients"><br><span
                    style="font-family: 'Gill Sans', 'Gill Sans MT', Calibri, 'Trebuchet MS', sans-serif;font-size: 26px;">Ingredients</span><br><br>
                <div class="grid_ingredients">
                    <div class="grid_ingredients_item" id="ingredients_col1">
"""
# add ingredients col 1
html9 = """
                    </div>
                    <div class="grid_ingredients_item" id="ingredients_col2">
"""
# add ingredients col 2
html10 = """
                    </div>
                    <div class="grid_ingredients_item" id="ingredients_col3">
"""
# add ingredients col 3
html11 = """
                    </div>
                </div>
            </div><br>
            <div class="recipe_instructions"><br><span
                    style="font-family: 'Gill Sans', 'Gill Sans MT', Calibri, 'Trebuchet MS', sans-serif;font-size: 26px;">Steps</span>
                <br>
                <br>
"""
# add steps
html12 = """
            </div>
        </div>
    </center>
    <script src="https://code.jquery.com/jquery-1.11.1.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/paho-mqtt/1.0.1/mqttws31.min.js"></script>
    <script src="https://www.gstatic.com/firebasejs/4.3.1/firebase.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/crypto-js/3.1.2/rollups/aes.js"></script>
    <script src="chat.js"></script>
</html>
"""

def ingredients_in_column(ingredients_list):
    n_ingredients = len(ingredients_list)
    n_ingredients_by_col, remainder = n_ingredients // 3, n_ingredients % 3
    extra_in_col_1 = 0 if remainder == 0 else 1
    extra_in_col_2 = 1 if remainder == 2 else 0
    limit_col1 = n_ingredients_by_col+extra_in_col_1
    limit_col2 = n_ingredients_by_col*2+extra_in_col_1+extra_in_col_2
    if limit_col1 == 1:
        col1 = [ingredients_list[0]]
    else:
        col1 = ingredients_list[:limit_col1]
    if (limit_col2 - limit_col1) == 1:
        col2 = [ingredients_list[limit_col1]]
    elif (limit_col2 - limit_col1) == 0:
        col2 = []
    else:
        col2 = ingredients_list[limit_col1:limit_col2]
    if n_ingredients - limit_col2 == 1:
        col3 = [ingredients_list[limit_col2]]
    elif n_ingredients - limit_col2 == 0:
        col3 = []
    else:
        col3 = ingredients_list[limit_col2:]
    return col1, col2, col3

def generate_card(i, rdata):
    urllib.request.urlretrieve(rdata["image_url"], "food/resources/img/recipe_img/"+i.__str__()+".jpg")

    prep_time = "--"
    if "Prep" in rdata["time_info"].keys():
        prep_time = rdata["time_info"]["Prep"]
    cook_time = "--"
    if "Cook" in rdata["time_info"].keys():
        cook_time = rdata["time_info"]["Cook"]
    total_time = "--"
    if "Total" in rdata["time_info"].keys():
        total_time = rdata["time_info"]["Total"]
    servings = "--"
    if "Servings" in rdata["time_info"].keys():
        servings = rdata["time_info"]["Servings"]

    col1, col2, col3 = ingredients_in_column(rdata['ingredients'])
    col1 = "<span>" + "</span><br><br><span>".join(col1) + "</span>"
    col1 = col1.replace("¾", "3/4")
    col1 = col1.replace("½", "&frac12")
    col1 = col1.replace("¼", "1/4")
    col1 = col1.replace("⅓", "1/3")
    col1 = col1.replace("⅛", "1/8")
    col2 = "<span>" + "</span><br><br><span>".join(col2) + "</span>"
    col2 = col2.replace("¾", "3/4")
    col2 = col2.replace("½", "&frac12")
    col2 = col2.replace("¼", "1/4")
    col2 = col2.replace("⅓", "1/3")
    col2 = col2.replace("⅛", "1/8")
    col3 = "<span>" + "</span><br><br><span>".join(col3) + "</span>"
    col3 = col3.replace("¾", "3/4")
    col3 = col3.replace("½", "&frac12")
    col3 = col3.replace("¼", "1/4")
    col3 = col3.replace("⅓", "1/3")
    col3 = col3.replace("⅛", "1/8")

    html_page = html1 + i.__str__()+".jpg" + html2 + rdata["title"] + html3 + "stars3.5.png" + html4 + "healthiness_green.png" + html5 + prep_time + html6 + cook_time + html7 + total_time + html8 + servings + html8_bis + rdata['description'] + html8_ter + col1 + html9 + col2 + html10 + col3 + html11 + rdata['description'] + html12

    f = open("food/resources/img/recipe_card/recipe"+i.__str__()+".html", "w")
    f.write(html_page)
    f.close()


if __name__ == "__main__":
    for i in range(10):
        with open(consts.json_xUsers_Xrecipes_path, 'r') as fjson:
            content = json.load(fjson)
        random_recipe_id = random.choice(list(content["recipes_data"].keys()))
        random_recipe_data = content['recipes_data'][random_recipe_id]
        generate_card(i, random_recipe_data)

