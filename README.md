
Amazfit bip tools
=================

This is a suite of tools to make easier to translate and tweak Amazfit bip (A1608) watch.


Usually each tool have its -h flag that allow you to understand better how it works.


Requirements:  
Python  2.7.x


res2img.py
----------

small tool to convert amazfit bip resource file to a standard image file.

./res2img.py -h  

./res2img.py -u [-a] [-i Mili_chaohu.res]  

  edit your bmp you will find in a new direcory freshly created  

./res2img.py -p [-i Mili_chaohu.res]

  repack the res file with new name  

if you call it without any parameter actually it will look for "Mili_chaohu.res_3.0.4"

it will generate splitted a number of raw file and for each file a correspondent png file.

*** The bip display has 8 colors only (black, white, red, green, blue, yellow, cyan, magenta)
The stock res only uses 0 or 255 as r g b values. 
If a resource uses transparent we translate this as 254,254,0 in the png
If a png uses 254,254,0 as first color we use it as transparent creating that resource ***  


zh-cn2en.py
----------

./zh-cn2en.py [-h] [-l en] [-p]

Process zh-cn2en.txt by looking for hex string pattern, connect to google translate and add the english translation to the txt file
this tool can be useful for replacing string from chinese to english


zh-check_translation.py
----------

It can help you check the translation (the length of translated strings must be less than or equal to the length of the chinese strings). It prints the line number where the problem occurred


zh-merge_old2new_trans.py
----------

If there will be a new zh-cn2(lang).txt file from next firmware upgrades, the tool can be used to merge your translations from the old "zh" file to the new one

