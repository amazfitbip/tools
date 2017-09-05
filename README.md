== res2img

./res2img.py [Mili_chaohu.res]

small tool to convert amazfit bip resource file to a standard image file.

if you call it without any parameter actually it will look for "Mili_chaohu.res_3.0.4"

it will generate splitted a number of raw file and for each file a correspondent jpg file.

The program generate some temporary file like a textual palette and a mask to be applied to the grayscale image to get the indexed one. By tweaking the program is possible to keep souch files.



== zh-cn2en

./zh-cn2en.py

Process zh-cn2en.txt by looking for hex string pattern, connect to google translate and add the english translation to the txt file
this tool can be useful for replacing string from chinese to english



== zh-check_translation

It can help you check the translation (the length of translated strings must be less than or equal to the length of the chinese strings). It prints the line number where the problem occurred



== zh-merge_old2new_trans

If there will be a new zh-cn2(lang).txt file from next firmware upgrades, the tool can be used to merge your translations from the old "zh" file to the new one

requirements:  
https://github.com/ssut/py-googletrans.git

