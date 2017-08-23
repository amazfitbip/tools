#!/usr/bin/python

#https://stackoverflow.com/questions/42381009/convert-arbitrary-bytes-to-any-lossless-common-image-format
#http://www.imagemagick.org/discourse-server/viewtopic.php?t=31451
#https://superuser.com/questions/294270/how-to-view-raw-binary-data-as-an-image-with-given-width-and-height

#https://askubuntu.com/questions/147554/what-software-can-display-raw-bitmaps-on-linux

#palette
#https://www.imagemagick.org/discourse-server/viewtopic.php?t=24682

#http://www.imagemagick.org/discourse-server/viewtopic.php?f=1&t=24193&hilit=clut

ver="4"

import sys, struct, os, md5, hashlib
fileName = "Mili_chaohu.res_3.0."+ver
if len(sys.argv) == 2:
    fileName = sys.argv[1]

#with open('abc.dat', 'rb') as fobj:
#    byte_string, n1, n4 = struct.unpack('4sbI', fobj.read(12)) 
#https://docs.python.org/3/library/struct.html#format-strings


with open(fileName, mode='rb') as file: # b is important -> binary
    fileContent = file.read()
    #https://docs.python.org/3/library/struct.html#format-strings
    fileHeader, version, dummy1, dummmy2 = struct.unpack('5sbHL', fileContent[0:16]) 

    if fileHeader != "HMRES":
	print "file isn't a resource file. Exiting"
	os.exit(1)
    print "file is a Haumi resource file"
    print "version??? %d" % version
    offset=16 #boh
    offset=19 +4

    map = []
    firstBitmapOffset=0
    while ( offset < len(fileContent) ):
	#print fileContent[offset:offset+2] 
	if fileContent[offset:offset+2] == "BM" and firstBitmapOffset == 0:
	    map.append(offset)
	    #print "DEBUG: identified bitmap at offset=%d" % offset

	if fileContent[offset:offset+1] == "BM":
	    firstBitmapOffset = offset+1
	    #break

#	print ":".join("{:02x}".format(ord(c)) for c in fileContent[offset:offset+4])
#        os.exit(1)
#	length=int("".join("{:02x}".format(ord(c)) for c in fileContent[offset:offset+4]),16)
#	map.append(length)
#	offset+=4
	#print "LEN",length #,"END",end
	offset+=1

    myoffset=firstBitmapOffset
    for index in range(len(map)):

	#if index != 293:
	#	continue
	#if index != 200:
	#	continue

	sys.stdout.write('.')
	sys.stdout.flush()
	#print 'Current fruit :', map[index]
	#print "DEBUG",myoffset
	start = map[index]
	try:
		end = map[index+1]
	except:
		end = -1

	m = hashlib.md5()
	m.update(fileContent[start:end])
	#filename = "%03d_%s_%s.bmp" % (index, m.hexdigest(), ver)

	unknown1 = ord(fileContent[start+4:start+5])

	unknown2 = ord(fileContent[start+6:start+7])

	raw_image_width = ord(fileContent[start+8:start+9])
	#filename = "%03d_%03d_%s" % (index, raw_image_width, ver)
	filename = "%03d_%02x_%02x_%s" % (index, unknown1, unknown2, ver)
	palette_len = ord(fileContent[start+12:start+13])
	#print DEBUG: palette_len=%d" % palette_len

	newFile = open(filename+".raw", "wb")
	#newFile = open(str(start)+"_"+str(end)+".bmp", "wb")
	#newFile = open("index_"+str(index)+"_"+str(start)+".bmp", "wb")
	# write to file
	newFile.write(fileContent[start:end])
	newFile.close()

	#newFile = open(filename+".raw", "wb")
	#newFile = open(str(start)+"_"+str(end)+".bmp", "wb")
	#newFile = open("index_"+str(index)+"_"+str(start)+".bmp", "wb")
	# write to file
	#newFile.write(fileContent[start+16+ ( palette_len * 4) :end])
	#newFile.close()

	raw_image = fileContent[start+16+ ( palette_len * 4) :end]
	raw_image_size = len(raw_image)
	raw_image_height = raw_image_size / raw_image_width

	#cmd = "convert -size "+str(raw_image_width)+"x"+str(raw_image_height)+"+"+str(16 + palette_len * 4) +" -depth 8 -format GRAY rgb:"+filename+".raw " +filename+".png"

	#working
	#cmd = "convert -size "+str(raw_image_width)+"x"+str(raw_image_height)+"+"+str(16 + palette_len * 4) +" -depth 8  -alpha off -compress NONE -scale 800% gray:"+filename+".raw " +filename+".jpg"

	#right proportion zoomed
	#cmd = "convert -size "+str(raw_image_width * 4)+"x"+str(raw_image_height)+"+"+str(16 + palette_len * 4) +" -depth 2  -alpha off -compress NONE -scale 800% gray:"+filename+".raw " +filename+".jpg"

	#right size unscaled
	#cmd = "convert -size "+str(raw_image_width * 4)+"x"+str(raw_image_height)+"+"+str(16 + palette_len * 4) +" -depth 2  -alpha off -compress NONE gray:"+filename+".raw " +filename+".jpg"

	palfile = open(filename+".pal","w")
	for i in range(palette_len):
	    #print "i: %x" %(16 + i)
	    r=ord(fileContent[start+16+ ( 4*i+0):start+16+ ( 4*i+1)])
	    g=ord(fileContent[start+16+ ( 4*i+1):start+16+ ( 4*i+2)])
	    b=ord(fileContent[start+16+ ( 4*i+2):start+16+ ( 4*i+3)])
	    a=ord(fileContent[start+16+ ( 4*i+3):start+16+ ( 4*i+4)])
	    #print "DEBUG: rgb(%d,%d,%d)" %(r,g,b)
	    if a != 0:
		print "DEBUG: alpha(%d)" %a
	    palfile.write("xc:rgb(%d,%d,%d)\n" % ( r,g,b))
	palfile.close()

	cmd="convert @"+filename+".pal +append "+filename+"clut.png"
	#print "DEBUG: %s" % cmd
	os.system(cmd)

	#print "DEBUG: removing "+filename+".pal"
	os.unlink(filename+".pal")

	cmd = "convert -size "+str(raw_image_width * 4)+"x"+str(raw_image_height)+"+"+str(16 + palette_len * 4) +" -depth 2  -alpha off -compress NONE gray:"+filename+".raw "+filename+"clut.png -clut " +filename+".jpg"
	#print "DEBUG: %s" % cmd
	os.system(cmd)

	#print "DEBUG: removing "+filename+".pal"
	os.unlink(filename+"clut.png")
	
	#myoffset = end
