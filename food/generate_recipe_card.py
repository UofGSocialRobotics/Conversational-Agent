import fpdf
import json
import random
import imgkit
import urllib.request


import food.resources.recipes_DB.allrecipes.nodejs_scrapper.consts as consts

img_dir_path = 'food/resources/recipes_DB/allrecipes/images/'


imgkit.from_url('/Users/lucileca/Desktop/Conversational_Agent/server_side/food/test.html', 'food/out.jpg', options={"enable-local-file-access": ""})

class HTML2PDF(fpdf.FPDF, fpdf.HTMLMixin):
    pass

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
                    src="
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
                    id="rstars_img" height="20px">
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
html7 = """
                </b>
                <span id="servings"> </span></div>
            <div class="recipe_description" id="recipe_description">
"""
# add description
html8 = """
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
# add description
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

def generate_card(rid, rdata):
    txt_ingredients = "\n".join(rdata['ingredients'])
    txt_instructions = "\n".join(rdata['instructions'])

    pdf = HTML2PDF()
    pdf.add_page()
    pdf.write_html(html1)
    pdf.set_font("Helvetica", size=12)
    pdf.write_html(html2)
    pdf.output("simple_demo.pdf")


if __name__ == "__main__":
    with open(consts.json_xUsers_Xrecipes_path, 'r') as fjson:
        content = json.load(fjson)
    random_recipe_id = random.choice(list(content["recipes_data"].keys()))
    random_recipe_data = content['recipes_data'][random_recipe_id]
    generate_card(random_recipe_id, random_recipe_data)


