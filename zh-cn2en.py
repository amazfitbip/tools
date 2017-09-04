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
parser.add_argument('-o', '--output', type=str, dest='output', help='output name of translation file, default zh-cn2en.txt')
parser.add_argument('-i', '--input', type=str, dest='input', help='input name of translation file, default zh-cn2en.txt', default='zh-cn2en.txt')
parser.add_argument('-t', '--auto_translate', action='store_true',dest='auto_translate', help='auto translate input file')
parser.add_argument('-m', '--manual_translate', action='store_true',dest='manual_translate', help='manually translate input file')
parser.add_argument('-f', '--fw', dest='firmwareFile', default="Mili_chaohu.fw", help='f (default:%(default)s)')
parser.add_argument('-v', dest='verbose', action='store_true', help='verbose')
parser.add_argument('-p', dest='patch', action='store_true', help='patch firmware file. You can patch firmware with auto translated text (-t), or with manually translated text (-m), or with input file only (with translation, which you manually made before)')
parser.add_argument('-a', dest='analyze', action='store_true', help='analyze input file')
#parser.add_argument("--type", default="toto", choices=["toto","titi"],
#                              help = "type (default: %(default)s)")
#parser.set_defaults(language='en', fw='Mili_chaohu.fw')
args = parser.parse_args()


if args.auto_translate and args.manual_translate:
	print 'ERROR: Invalid parameter combination (-t -m)'
	print parser.print_help()
	sys.exit(1)

inputTxtFileName = args.input

if args.output:
    outputTxtFileName = args.output
else:
    outputTxtFileName = args.input

translation_tuples = []
for_translation = []
with open(inputTxtFileName, mode='r') as file:
    tmp=file.readline().rstrip('\n').lstrip('#')
    string_fw=tmp.split(':')[0]
    safe_address=tmp.split(':')[1]
    for l in file:
	line=l.lstrip('#').rstrip('\n')
	addrs_s, string_hex, string_cn, string_en = line.split("|")

	addrs_ar= [int(c,16) for c in addrs_s.split(",")]
	if not string_hex and string_cn:
	    string_hex=" ".join( [ "%02x" % ord( x ) for x in string_cn ]).upper()
	else:
	    string_hex=" ".join(c for c in string_hex.split())
	    string_cn="".join(c for c in string_hex.split()).decode("hex")
	if len(string_en) == 0:
	    string_en=''

	for_translation.append((addrs_ar, string_hex, string_cn, string_en, addrs_s))

if args.auto_translate:
	out_lines = []
	for item in for_translation:
		line_header=""

		addrs_ar, string_hex, string_cn, _, _ = item
		if _ and inputTxtFileName == outputTxtFileName:
	    		string_translated=_
		else:
	    		string_translated=translator.translate(string_cn, dest=args.language).text

		# update translation file
		if len(string_translated) > len(string_cn):
			line_header = "#"

		translation_tuple = tuple( [string_hex, string_translated,addrs_ar])
		if len(string_translated) <= len(string_cn) and translation_tuple not in translation_tuples:
			translation_tuples.append(translation_tuple)

		out_lines.append("%s%s|%s|%s|%s\n" % (line_header, ",".join(["%08X" % c for c in addrs_ar]),string_hex, string_cn, string_translated))

		print "%s%s => %s(%d) = %s(%d)" % (line_header, string_hex,string_cn,len(string_cn),string_translated,len(string_translated))

	with open(outputTxtFileName, 'w') as file:
		file.write("#%s:%s\n" % (string_fw, safe_address))
		for line in out_lines:
			file.write(line)

elif args.manual_translate:

	print "\n\n\n==== Translate strings (lenght must be equal or lower than CN lenght) ====\nKeep translation from file - Press Enter only\n\n\n"
	cnt = 1
	man_translated = []
	for item in for_translation:
		addrs_ar, string_hex, string_cn, string_other, addrs_s = item

		while True:
			print '%d/%d: CN: %s (%d), From file: %s (%d): ' % (cnt, len(for_translation), string_cn, len(string_cn), string_other, len(string_other))
			print '%s%s' % (''.join([' ']*(len(item[2])-1)), 'v - STOP HERE (max len - %s)' % len(string_cn))
			translation = raw_input()
			if len(translation) > len(string_cn):
				print "Translation lenght is greather than CN string (%d) > (%d). Try it again: " % (len(translation), len(string_cn))
			elif len(translation) == 0:
				man_translated.append(item)
				break
			else:
				man_translated.append((item[0:-1] + (translation,)))
				break
		cnt += 1
	# after tranlation, we save the file
	with open(outputTxtFileName, 'w') as file:
		file.write("#%s:%s\n" % (string_fw, safe_address))
		for item in man_translated:
			file.write("%s|%s|%s|%s\n" % (item[4], item[1], item[2], item[3]))
			# rewrite translation tuples
			translation_tuples.append((item[1], item[3], item[0]))
		print "Translation saved to '%s'. You can use it for patch firmware (-p -i %s)" % (outputTxtFileName, outputTxtFileName)

else:
	for item in for_translation:
                addrs_ar, string_hex, string_cn, string_other, _ = item

                translation_tuple = tuple( [string_hex, string_other,addrs_ar])
                if len(string_other) <= len(string_cn) and translation_tuple not in translation_tuples:
                        translation_tuples.append(translation_tuple)

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

	    if translation_tuples_s[index][2][0] != 1 and ix not in (translation_tuples_s[index][2]):
		print('0x%s %s (%s) SKIPPED (unsafe) at %08X not in %s' % (find_str_user_friendly, find_str.decode("hex"), translation_tuples_s[index][1], ix, ",".join(["%08X" % c for c in translation_tuples_s[index][2]])))
    		ix += len(find_str.decode("hex")) # +2 because len('ll') == 2
		continue

	    #avoid wrong substitution
	    if ord(s_ar[ix+len(find_str.decode("hex"))]) != 0 or (string_fw == version and ix < int(safe_address,16) and ix not in (translation_tuples_s[index][2])):
		print('0x%s %s (%s) SKIPPED (unsafe) at %x :-|' % (find_str_user_friendly, find_str.decode("hex"), translation_tuples_s[index][1], ix))
    		ix += len(find_str.decode("hex")) # +2 because len('ll') == 2
		continue

	    found_cnt+=1
	    len_addrs=len(translation_tuples_s[index][2])
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

