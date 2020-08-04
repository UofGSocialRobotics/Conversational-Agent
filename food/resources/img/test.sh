for f in /Users/lucileca/Desktop/Conversational_Agent/server_side/food/resources/img/recipe_card/*.html;
    do echo $f;
    webkit2png file://$f -F --delay=1;
done
#for f in /Users/lucileca/Desktop/Conversational_Agent/server_side/food/resources/img/recipe_card/*clipped.png;
#    do rm $f;
#done
#for f in /Users/lucileca/Desktop/Conversational_Agent/server_side/food/resources/img/recipe_card/*thumb.png;
#    do rm $f;
#done
for f in /Users/lucileca/Desktop/Conversational_Agent/server_side/food/resources/img/recipe_card/*.png;
    do echo $f;
done
