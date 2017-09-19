#!/usr/bin/python

###########################################
#
# palette remap only for indexed png
#
# example:  pngcolor "255,255,0-255,255,255;255,0,0-255,0,255" file1 [file2 [file3 ........] ] 
#		change yellow to white and red to magenta
#
###########################################

import sys, struct, zlib

list_from=[]
list_to=[]

def usage(error):
	print error
	print
	exit()

if len(sys.argv)<3:
	usage(sys.argv[0]+" r,g,b-r,g,b[;r,g,b-r,g,b.....] file1 [file2 .... ]")


print "--Changes: "

for change in sys.argv[1].split(";"):
	print "Color change :"+change
	fromto=change.split("-")
	#print fromto

	if len (fromto)==2:
		color_from=fromto[0].split(",")
		color_to=fromto[1].split(",")
		if len(color_from)==3 and len (color_to)==3 :
			try:
				list_from.append([int(color_from[0]),int(color_from[1]),int(color_from[2])])
				list_to.append  ([int(color_to[0]),  int(color_to[1]),  int(color_to[2])])
			except:
				usage("wrong int value in: "+change)
		else :
			usage("error: insert 3 colors in format r,g,b-r,g,b in: "+change)
	else:
		usage("error: insert 3 colors in format r,g,b-r,g,b in: "+change)

for index in range(2,len(sys.argv)):
	print "\n--File: "+sys.argv[index]
	
	with open(sys.argv[index], mode='r+b') as fileRW: # b is important -> binary
		fileContent = fileRW.read()
		size=0
		start=-4
		chunk=''
		changed=0
		palette=''
		while chunk != "IEND" and changed==0:
			start+=(12+size)
			size,chunk = struct.unpack('>i4s', fileContent[start:start+8])
			if chunk=="PLTE":
				for color in range(0, (size/3) ):
					r, g, b= struct.unpack('BBB', fileContent[start+8+color*3:start+8+color*3+3])
					for colnum in range(0,len(list_from)):
						if [r,g,b] == list_from[colnum]:
							print "\t Changed: %d,%d,%d ->"%(r,g,b)
							pos=start+8+color*3;
							color_from=list_from[colnum]
							changed=1
							r=list_to[colnum][0]
							g=list_to[colnum][1]
							b=list_to[colnum][2]
					print "Color ok: %d,%d,%d"%(r,g,b)
					palette+=chr(r)
					palette+=chr(g)
					palette+=chr(b)

				if changed==1:
					palette="PLTE"+ palette
					fileRW.seek(start+4)
					fileRW.write(palette)
					fileRW.write(struct.pack('>i',zlib.crc32(palette)))
					
					

