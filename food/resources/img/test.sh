for f in /Users/lucileca/Desktop/Conversational_Agent/server_side/food/resources/img/recipe_card/*.html;
    do echo $f;
    webkit2png file://$f;
done
