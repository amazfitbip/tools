#!/usr/bin/python
# -*- coding: utf-8 -*-

import os,sys,argparse
reload(sys)  
sys.setdefaultencoding('utf8')

from googletrans import Translator
translator = Translator()
#translator.translate('안녕하세요.')
# <Translated src=ko dest=en text=Good evening. pronunciation=Good evening.>
#print translator.translate('안녕하세요.', dest='en')
#.decode("hex")


parser = argparse.ArgumentParser(description='Auto-translate and patch firmware files')
parser.add_argument('-l', '--language', dest='language', help='en|it|de ...', required=True)
parser.add_argument('-o', '--output')
parser.add_argument('-v', dest='verbose', action='store_true', help='patch firmware file')
parser.add_argument('-a', dest='analyze', action='store_true', help='analyze input file')
#parser.set_defaults(language='en', baz='badger')
args = parser.parse_args()

print args.language
#sys.exit(12)

##TODO
## the pattern must be ordered from the longer to the shorter 
## each pattern must be searched into the binary + 00 and replaced with the new string + 00 

#https://wiki.python.org/moin/HowTo/Sorting
#>>> student_tuples = [
#        ('john', 'A', 15),
#        ('jane', 'B', 12),
#        ('dave', 'B', 10),
#]
#>>> sorted(student_tuples, key=lambda student: student[2])   # sort by age
#[('dave', 'B', 10), ('jane', 'B', 12), ('john', 'A', 15)]


fileName = "zh-cn2en.txt"

translation_tuples = []

out = open("zh-cn2en.out", mode='w')
with open(fileName, mode='r') as file:
    for l in file:
	line=l.lstrip('#').rstrip('\n')
	string_hex=" ".join(c for c in line.split("|")[0].split())
	string_cn="".join(c for c in string_hex.split()).decode("hex")
	if len(line.split("|")) == 2:
	    string_en=line.split("|")[1]
	    #check here if translation is longer then the original hex
	else:
	    string_en=translator.translate(string_cn, dest='en').text

	# update translation file
	if len(string_en) > len(string_cn):
	    string_hex = "#"+string_hex

	translation_tuple = tuple( [string_hex, string_en])
	if len(string_en) <= len(string_cn) and translation_tuple not in translation_tuples:
	    translation_tuples.append(translation_tuple)

	out.write("%s|%s\n" % (string_hex, string_en))
	print "%s => %s(%d) = %s(%d)" % (string_hex,string_cn,len(string_cn),string_en,len(string_en))

translation_tuples_s = sorted(translation_tuples, key=lambda string_cn: len(string_cn[0]), reverse=True)

if args.verbose:

    firmwareFile = "Mili_chaohu.fw"

    with open(firmwareFile, "rb") as input_file:
        s = input_file.read()

    for index in range(len(translation_tuples_s)):
	print translation_tuples_s[index]

	from bitstring import ConstBitStream
	from bitstring import BitArray

	# Can initialise from files, bytes, etc.
	#s = ConstBitStream(filename='Mili_chaohu.fw')
	# Search to Start of Frame 0 code on byte boundary
	#found = s.find('0xffc0', bytealigned=True)

	find_str = "".join(c for c in translation_tuples_s[index][0].split())
	ix = 0
	s_ar=list(s)
	while ix < len(s):
    	    ix = s.find(find_str.decode("hex"), ix)
    	    if ix == -1:
    	        break
    	    print('%s found at %d' % (find_str.decode("hex"), ix))
    
    	    for r in range(len(find_str.decode("hex"))):
	        if r < len(translation_tuples_s[index][1]):
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
	    
    with open(firmwareFile.replace(".fw","_EN.fw"), "wb") as output_file:
        output_file.write(s)
	sys.exit(12)

	#url =  "%".join(c for c in line.split())
	#print "%".join("{:02x}".format(ord(c)) c for c in line)
	#print "%".join("{:02x}".format(cord(c)) for c in line.split())
	#print gurl+url
	#os.system("curl -A 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:36.0) Gecko/20100101 Firefox/36.0' "+gurl+url)
os.rename('zh-cn2en.out', 'zh-cn2en.txt')
