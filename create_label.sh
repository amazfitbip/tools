#convert -list font 
#font=Droid-Sans
#font=DejaVu-Sans-Condensed
#font=DejaVu-Serif-Condensed

font=DejaVu-Sans
#run outdoor
 convert -background black -fill white  -font $font -gravity center \
          -size 32x21  label:"Run\noutdoor"     323.png

#run indoor
 convert -background black -fill white  -font $font -gravity center \
          -size 32x21  label:"Run\nindoor"     321.png