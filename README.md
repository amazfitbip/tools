small tool to convert amazfit bip resource file to a standard image file.

./res2img.py [Mili_chaohu.res]

if you call it without any parameter actually it will look for "Mili_chaohu.res_3.0.4"

it will generate splitted a number of raw file and for each file a correspondent jpg file.

The program generate some temporary file like a textual palette and a mask to be applied to the grayscale image to get the indexed one. By tweaking the program is possible to keep souch files.

