#!/usr/bin/python
# -*- coding: utf-8 -*-

import os,sys,argparse,re
reload(sys)  
sys.setdefaultencoding('utf8')

from googletrans import Translator
translator = Translator()
#translator.translate('안녕하세요.')
# <Translated src=ko dest=en text=Good evening. pronunciation=Good evening.>
#print translator.translate('안녕하세요.', dest='en')
#.decode("hex")


parser = argparse.ArgumentParser(description='Auto-translate and patch firmware files')
parser.add_argument('-l', '--language', dest='language', default="en", #choices=["en","it"], 
					help='l (default:%(default)s)' #, required=True
		    )
parser.add_argument('-o', '--output')
parser.add_argument('-f', '--fw', dest='firmwareFile', default="Mili_chaohu.fw", help='f (default:%(default)s)')
parser.add_argument('-v', dest='verbose', action='store_true', help='verbose')
parser.add_argument('-p', dest='patch', action='store_true', help='patch firmware file')
parser.add_argument('-a', dest='analyze', action='store_true', help='analyze input file')
#parser.add_argument("--type", default="toto", choices=["toto","titi"],
#                              help = "type (default: %(default)s)")
#parser.set_defaults(language='en', fw='Mili_chaohu.fw')
args = parser.parse_args()

if os.path.isfile("zh-cn2"+args.language+".txt"):
    fileName = "zh-cn2"+args.language+".txt"
    targetFileName = "zh-cn2"+args.language+".txt"
    tmpFileName = fileName.replace(".txt",".tmp")
    defaultlang = args.language
else:
    fileName = "zh-cn2en.txt"
    targetFileName = "zh-cn2"+args.language+".txt"
    tmpFileName = fileName.replace(".txt",".tmp")
    defaultlang = "en"


translation_tuples = []
out = open(tmpFileName, mode='w')
with open(fileName, mode='r') as file:
    for l in file:
	line_header=""
	line=l.lstrip('#').rstrip('\n')
	string_fw=line.split("|")[0]
	string_addrs=line.split("|")[1]
	string_hex=" ".join(c for c in line.split("|")[2].split())
	string_cn="".join(c for c in string_hex.split()).decode("hex")

	#cleanup translation when switching to other language
	if len(line.split("|")) == 5 and defaultlang == args.language:
	    string_translated=line.split("|")[4]
	    #check here if translation is longer then the original hex
	else:
	    string_translated=translator.translate(string_cn, dest=args.language).text

	# update translation file
	if len(string_translated) > len(string_cn):
	    line_header = "#"

	translation_tuple = tuple( [string_hex, string_translated,string_addrs])
	if len(string_translated) <= len(string_cn) and translation_tuple not in translation_tuples:
	    translation_tuples.append(translation_tuple)

	out.write("%s%s|%s|%s|%s|%s\n" % (line_header, string_fw,string_addrs,string_hex, string_cn, string_translated))

	print "%s%s => %s(%d) = %s(%d)" % (line_header, string_hex,string_cn,len(string_cn),string_translated,len(string_translated))

os.rename(tmpFileName, targetFileName)

#sort the translation array to be sure to patch the short string later as they can be included in longer one
translation_tuples_s = sorted(translation_tuples, key=lambda string_cn: len(string_cn[0]), reverse=True)

if args.patch:

    version = "unknown"    
    if not args.firmwareFile:
	print "ERROR: missing --fw <firmwarefile>"
	sys.exit(1)

    with open(args.firmwareFile, "rb") as input_file:
        s = input_file.read()

    m = re.search('@([0-9].[0-9].[0-9].[0-9]+)', s)
    if m:
	version =  m.group(1)
	print "Detected firmare version %s" % version

    for index in range(len(translation_tuples_s)):
	#print translation_tuples_s[index]

	#from bitstring import ConstBitStream
	#from bitstring import BitArray

	# Can initialise from files, bytes, etc.
	#s = ConstBitStream(filename='Mili_chaohu.fw')
	# Search to Start of Frame 0 code on byte boundary
	#found = s.find('0xffc0', bytealigned=True)

	find_str_user_friendly = " ".join(c for c in translation_tuples_s[index][0].split())
	find_str = "".join(c for c in translation_tuples_s[index][0].split())
	ix = 0
	s_ar=list(s)
	found_cnt=0
	while ix < len(s):
    	    ix = s.find(find_str.decode("hex"), ix)

    	    if ix == -1:
		if found_cnt == 0:
		    print('0x%s %s (%s) NOT FOUND :-(' % (find_str_user_friendly, find_str.decode("hex"), translation_tuples_s[index][1]))
    	        break

	    #avoid wrong substitution
	    if ord(s_ar[ix+len(find_str.decode("hex"))]) != 0 or (version == "0.0.8.74" and ix < int("00066050",16)):
		print('0x%s %s (%s) SKIPPED (unsafe) at %x :-|' % (find_str_user_friendly, find_str.decode("hex"), translation_tuples_s[index][1], ix))
    		ix += len(find_str.decode("hex")) # +2 because len('ll') == 2
		continue

	    found_cnt+=1
	    len_addrs=len((translation_tuples_s[index][2]).split(","))
	    warning=""
	    if found_cnt >len_addrs:
		warning="!!!!!!!!!!!!!"
    	    print('0x%s %s (%s) found at %x (%d/%d)%s' % (find_str_user_friendly, find_str.decode("hex"), translation_tuples_s[index][1], ix, found_cnt, len_addrs,warning))
    
    	    for r in range(len(find_str.decode("hex"))):
	        if r < len(translation_tuples_s[index][1]):
		    #print('0x%s %s (%s) found at %x (%d/%d)%s' % (find_str_user_friendly, find_str.decode("hex"), translation_tuples_s[index][1], ix+r, found_cnt, len_addrs,warning))
	    	    s_ar[ix+r] = (translation_tuples_s[index][1])[r]
	        else:
		    s_ar[ix+r] = chr(0)

    	    ix += len(find_str.decode("hex")) # +2 because len('ll') == 2

	s="".join(s_ar)

	#replace_str =  '{0:<0{1}x}'.format(int(translation_tuples_s[index][1].encode('hex'),16),len(find_str.decode('hex'))+2)
	#print "A ", find_str, len(find_str.decode('hex'))
	#print "B ", replace_str, len(replace_str.decode('hex'))

#	results = s.findall(find_str, bytealigned=True)
#https://github.com/sans-dfir/sift-files/blob/master/scripts/pe_carve.py
#	for i in results:
#	    print("Found start code at byte offset %d." % (int(i)/8))
#	    s0f0, length, bitdepth, height, width = s.readlist('hex:16, uint:16,   uint:8, 2*uint:16')
#	    print("Width %d, Height %d" % (width, height))

#https://stackoverflow.com/questions/29624398/searching-and-replacing-in-binary-file
	#s = s.replace((find_str+"00").decode("hex"),(replace_str+"00").decode("hex"))

	#DEBUG: just replace few occurrences
	#if index == 2:
	#    break
	    
    with open("Mili_chaohu_" +version + "_"+ args.language + ".fw", "wb") as output_file:
        output_file.write(s)
	sys.exit(0)

