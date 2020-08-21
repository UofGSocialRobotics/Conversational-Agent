#for f in /Users/lucileca/Desktop/Conversational_Agent/server_side/food/resources/img/recipe_card/small/HTMLs/*.html;
#    do echo $f;
#    webkit2png file://$f -F --delay=1;
#done
#for f in /Users/lucileca/Desktop/Conversational_Agent/server_side/food/resources/img/recipe_card/*clipped.png;
#    do rm $f;
#done
for f in /Users/lucileca/Desktop/Conversational_Agent/server_side/food/resources/img/recipe_card/small/PNGs/*.png;
    do echo $f;
    filename=$(basename -- "$f");
    filename="${filename%.*}";
#    echo $filename;
#    echo $xpath;
    pngquant 64 $f -o reduced$filename.png
done
