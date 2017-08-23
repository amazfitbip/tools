#!/usr/bin/python
# -*- coding: utf-8 -*-

import os,sys
reload(sys)  
sys.setdefaultencoding('utf8')

from googletrans import Translator
translator = Translator()
#translator.translate('안녕하세요.')
# <Translated src=ko dest=en text=Good evening. pronunciation=Good evening.>
#print translator.translate('안녕하세요.', dest='en')
#.decode("hex")


fileName = "ch2en.txt"

out = open("ch2en.out", mode='w')
with open(fileName, mode='r') as file:
    for l in file:
	line=l.rstrip('\n')
	string_hex=line.split("|")[0]
	string_cn="".join(c for c in string_hex.split()).decode("hex")
	if len(line.split("|")) == 2:
	    string_en=line.split("|")[1]
	    out.write(line+"\n")
	    
	else:
	    string_en=translator.translate(string_cn, dest='en').text
	    out.write(line+"|"+string_en+"\n")

	print "%s => %s = %s" % (string_hex,string_cn,string_en)

	#url =  "%".join(c for c in line.split())
	#print "%".join("{:02x}".format(ord(c)) c for c in line)
	#print "%".join("{:02x}".format(cord(c)) for c in line.split())
	#print gurl+url
	#os.system("curl -A 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:36.0) Gecko/20100101 Firefox/36.0' "+gurl+url)
os.rename('ch2en.out', 'ch2en.txt')
