#!/usr/bin/python

#TODO
#switch to pil
#https://stackoverflow.com/questions/29433243/convert-image-to-specific-palette-using-pil-without-dithering
#list_of_pixels = list(im.getdata())
# Do something to the pixels...
#im2 = Image.new(im.mode, im.size)
#im2.putdata(list_of_pixels)

#https://stackoverflow.com/questions/42381009/convert-arbitrary-bytes-to-any-lossless-common-image-format
#http://www.imagemagick.org/discourse-server/viewtopic.php?t=31451
#https://superuser.com/questions/294270/how-to-view-raw-binary-data-as-an-image-with-given-width-and-height

#https://askubuntu.com/questions/147554/what-software-can-display-raw-bitmaps-on-linux

#palette
#https://www.imagemagick.org/discourse-server/viewtopic.php?t=24682

#http://www.imagemagick.org/discourse-server/viewtopic.php?f=1&t=24193&hilit=clut


import sys, struct, os, md5, hashlib, argparse, time, datetime, subprocess, re, zlib
import logging

if len(sys.argv) == 2:
	fileName = sys.argv[1]

parser = argparse.ArgumentParser(description='Auto-translate and patch firmware files')
parser.add_argument('-l', '--language', dest='language', default="en", #choices=["en","it"],.
					help='l (default:%(default)s)' #, required=True
		    )
#parser.add_argument('-o', '--output', type=str, dest='output', help='output name of translation file, default zh-cn2en.txt')
parser.add_argument('-i', '--input', type=str, dest='input', help='input name of resource file (default:%(default)s)', default='Mili_chaohu.res')
parser.add_argument('-a', '--auto_translate', action='store_true', dest='translate', help='auto translate resource file using known dict')

parser.add_argument('-u', dest='unpack', action='store_true', help='unrepack the res file')
parser.add_argument('-p', dest='pack', action='store_true', help='repack the res file')
parser.add_argument('-d', dest='debug', action='store_true', help='debug')

#parser.add_argument('-m', '--manual_translate', action='store_true',dest='manual_translate', help='manually translate input file')
#parser.add_argument('-f', '--fw', dest='firmwareFile', default="Mili_chaohu.fw", help='f (default:%(default)s)')
#parser.add_argument('-v', dest='verbose', action='store_true', help='verbose')
#parser.add_argument('-p', dest='patch', action='store_true', help='patch firmware file. You can patch firmware with auto translated text (-t), or with manually translated text (-m), or with input file only
#parser.add_argument('-a', dest='analyze', action='store_true', help='analyze input file')
#parser.add_argument("--type", default="toto", choices=["toto","titi"],
#                              help = "type (default: %(default)s)")
#parser.set_defaults(language='en', fw='Mili_chaohu.fw')
args = parser.parse_args()

if args.debug:
	logging.basicConfig(level=logging.DEBUG)

if not (args.pack or args.unpack):
	logging.error("No parameter specified")
	print parser.print_help()
	sys.exit(1)

fileName = args.input

dirName = "_"+fileName

#with open('abc.dat', 'rb') as fobj:
#    byte_string, n1, n4 = struct.unpack('4sbI', fobj.read(12)) 
#https://docs.python.org/3/library/struct.html#format-strings

if not os.path.exists(dirName):
	os.mkdir(dirName)

strings_cn = {
	181: "Mon",
	182: "Wed",
	183: "Tue",
	184: "Fri",
	185: "Sat",
	186: "Day", #"Sun",
	187: "Thu",
	188: "Sun", #"Dau",

	#timer menu
	112: "B sync'ed",
	#360: "B sync'ed",
	113: "x disconn",
	#361: "x disconn",

	#Main menu
	294: "Alarm",
	296: "Compass",
	298: "Setup",
	300: "Activity",
	302: "Home",
	304: "Timer",
	306: "Weather",

	#timer menu
	308: "Countdown",
	310: "Stop\nwatch",

	#Activity menu
	 94: "Sports set",
	317: "Riding",
	319: "History",
	321: "Indoor\nrun",
	323: "Outdoor\nrun",
	325: "Walking"

	#345-362 Cinese2

}


def get_rsrc_addr(idx):
	ptr = (4 * idx + 0x14)
	buf = [ ord(elem) for elem in fileContent[ptr:ptr+4]]
	addr = (buf[0] <<0) + (buf[1] <<8) + (buf[2] << 16) + (buf[3] <<24)
	return addr

def png2raw(idx):
	warn=''

	raw="%s%s%03d.%s" % (dirName , os.path.sep , idx, "raw")
	img="%s%s%03d.%s" % (dirName , os.path.sep , idx, "png")

	#the png has been edited... recreate the new raw and load in memory

	#if os.path.getmtime(raw)  != os.path.getmtime(img) +20 :
	if os.path.getmtime(raw)  != os.path.getmtime(img) +0 :
		print "resource %3d | addr: %x " % ( index, offset )
		with open(img, mode='rb') as fileRead: # b is important -> binary
			fileContent = fileRead.read()
			fileHeader = struct.unpack('8s', fileContent[0:8])
			png_header = [ 0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a ]

			if fileContent[0:8] != (''.join(chr(l) for l in png_header)):
				print "ERROR: %d isn't a png resource" % idx
				return 1

			rawnew=open(raw, mode='wb')

			start=-4
			palette= []
			size=0
			transp=0
			chunk=""
			row_len=0
			data=""
			while chunk != "IEND":
				start+=(12+size)
				size,chunk = struct.unpack('>i4s', fileContent[start:start+8])
				#print 'DEBUG png: chunk: '+str(chunk)+" start: "+str(start)+' size: '+str(size)+' +12'
				#print ":".join("{:02x}".format(ord(c)) for c in (fileContent[start:start+8]))

				# PNG chunk type IHDR
				if chunk=="IHDR":
					width, height, depth, color, comp, filt, inter = \
							struct.unpack('>iibbbbb', fileContent[start+8:start+8+size])
					row_len=int( width*depth/8.0 +.99)
					png_colors=pow(2,depth)
					if (color, comp, filt, inter) != (3,0,0,0) :
						print "ERROR: %d isn't a color indexed image" % idx
						return 1
					#print width,depth,row_len
					#logging.debug("rowlen %x ")%row_len #rgb(%3x,%3x,%3x)" %(row_len, r,g,b))
				# PNG chunk type sRGB
				#if chunk=="sRGB":
				# PNG chunk type PLTE .. palette
				if chunk=="PLTE":
					colors_number=(size/3)
					for color in range(0, colors_number): 
						r, g, b= struct.unpack('BBB', fileContent[start+8+color*3:start+8+color*3+3])
						palette.extend( (r, g, b, 0) )
						logging.debug("colormap %3x: rgb(%3x,%3x,%3x)" %(color, r,g,b))
					if palette[0:3]==[254, 254, 0]:
						#if first colormap entry is 254 254 0 => we consider it as transparent
						logging.debug("transparent")
						palette[0:3]=[255, 255, 0]
						transp=1

					if colors_number > 9:
						warn="ERROR:--- RES %d HAS %d COLORS (Bip has 8:blk wht red grn blu yel mag cyan)\n"%(index,colors_number)

					stride=int(int(width) * int(depth) / 8) + ((int(width) * int(depth) )% 8 > 0)
					header_bmp = [ 0x42, 0x4D, 0x64, 0x00, int(width), 0x00, int(height) , 0x00, 
							stride, 0x00, int(depth) , 0x00, len(palette) /4, 0,int(transp), 0 ]
					header_bmp.extend(palette)
					try:
						rawnew.write("".join(chr(e) for e in header_bmp))
					except ValueError:
						print warn
						return 1

				# PNG chunk type IDAT 
				if chunk=="IDAT":
					data+=fileContent[start+8:start+8+size]

			expand=zlib.decompress(data)

			pos=0
			while (pos < len(expand)):
				rawnew.write(expand[pos+1:pos+1+row_len])
				pos+=1+row_len
				
			
			rawnew.close()
	else:
		# same mtime
		pass


	with open(raw, mode='rb') as rawimg:
		img = [ord(c) for c in rawimg.read()]

	return (img,warn)

def raw2png(idx):
	####################	
	# What I understand:
	# 
	# a color can be on or off; 
	# so the three byte are in fact 3 bits and we have 8 colors
	# to show other colors the faces use dithering
	#
	# trick: in case of transparency we set the first color at 254, 254, 0
	# 
	# works only on indexed png at the moment
	#
	####################

	start = offs + get_rsrc_addr(idx)
	if idx < max_rsrc:
		end = offs + get_rsrc_addr(idx + 1)
	else:
		end = -1

	if fileContent[start:start+2] != "BM":
		print "ERROR: %d isn't a bitmap resource" % idx
		return 1

	m = hashlib.md5()
	m.update(fileContent[start:end])


	width = ord(fileContent[start+4:start+5])
	height = ord(fileContent[start+6:start+7])
	stride = ord(fileContent[start+8:start+9])
	depth = ord(fileContent[start+0xa:start+0xb])
	colors = ord(fileContent[start+0xc:start+0xd])
	transp = ord(fileContent[start+0xe:start+0xf])

	print "idx: %d - depth %d bpp - w: %d - h: %d - ??? %d " % (idx, depth, width, height, transp)

	filename = dirName +  os.path.sep + "%03d" % (idx)
	palette_len = ord(fileContent[start+12:start+13])
	#print DEBUG: palette_len=%d" % palette_len

	newFile = open(filename+".raw", "wb")
	# write to file
	newFile.write(fileContent[start:end])
	newFile.close()

	raw_image = fileContent[start+16+ ( palette_len * 4) :end]
	raw_image_size = len(raw_image)

	if args.translate and idx in list(strings_cn.keys()):
		string = strings_cn[idx]
		print "translating %d with %s" % (idx, string)
		cmd = "convert -depth " + str(depth) + " -alpha off -compress NONE -background black -fill white -font DejaVu-Sans -gravity center -pointsize 9 -size "+str(width)+"x"+str(height)+"  label:\"" + string + "\" -define png:color-type=3 " +filename+".png 2>/dev/null"
		os.system(cmd)
		os.utime(filename+".png", (mtime+60, mtime+60))  # Set access/modified times in the future 
	elif fileContent[start:start+3] == "BMd" and palette_len <16:
		checksum=0
		pngfile =open(filename+".png","wb")
		# PNG header
		png_header = [ 0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a ]
		pngfile.write(''.join(map(chr,png_header)))
		# PNG chunk iHDR 
		iHDR_len =  [ 0x00, 0x00, 0x00, 0x0d]
		iHDR_chunk = [ 0x49, 0x48, 0x44, 0x52, 0x00, 0x00, 0x00, int(width), \
				0x00, 0x00, 0x00,  int(height), int(depth), 0x03, 0,0,0 ]
		iHDR_crc=zlib.crc32(''.join(map(chr,iHDR_chunk)))
		pngfile.write(''.join(chr(i) for i in iHDR_len))
		pngfile.write(''.join(chr(i) for i in iHDR_chunk))
		iHDR_str= struct.pack('>i',iHDR_crc)
		pngfile.write(iHDR_str)
		# PNG chunk sRGB
		sRGB_chunk= '\x00\x00\x00\x01\x73\x52\x47\x42\x00\xae\xce\x1c\xe9'
		pngfile.write(sRGB_chunk)

		row_len=int( width*depth/8.0 +.99)

		png_colors=pow(2,depth)

		# PNG chunk PLTE: palette
		PLTE_chunk=''

		for i in range(palette_len):
			r=ord(fileContent[start+16+ ( 4*i+0):start+16+ ( 4*i+1)])
			g=ord(fileContent[start+16+ ( 4*i+1):start+16+ ( 4*i+2)])
			b=ord(fileContent[start+16+ ( 4*i+2):start+16+ ( 4*i+3)])
			a=ord(fileContent[start+16+ ( 4*i+3):start+16+ ( 4*i+4)])
			logging.debug("colormap %3x: rgb(%3x,%3x,%3x)" %(i, r,g,b))
			PLTE_chunk+=chr(r)+chr(g)+chr(b)
			if a != 0:
			 	logging.debug("alpha(%d)" %a)
				
		if transp==1:
			logging.debug("transp")
			PLTE_chunk='\xfe\xfe\x00'+PLTE_chunk[3:]

		PLTE_len='\x00\x00\x00'+chr(len(PLTE_chunk))
		PLTE_chunk="PLTE"+ PLTE_chunk

		# write palette
		pngfile.write(PLTE_len)
		pngfile.write(PLTE_chunk)
		PLTE_crc=zlib.crc32(PLTE_chunk)
		PLTE_str= struct.pack('>i',PLTE_crc)
		pngfile.write(PLTE_str)
		# PNG chunk IDAT
		# Only one chunk for a little file
		#pngfile.write( struct.pack('>i',(row_len+1)*height+11))  #data len
		# zlib header: 3 win size, 8 deflate, 00 compress 0 dict 10001 check, 00000001 last
		#pngfile.write('IDAT\x38\x11\x01')
		#pngfile.write( struct.pack('<H',(row_len+1)*height))  #data len
		#pngfile.write( struct.pack('<H',65535-(row_len+1)*height))  #data len

		begin=start+16+ ( palette_len * 4) 

		data=''
		for row in range (0,height):
			#pngfile.write        ('\00'+fileContent[begin:begin+(row_len)])
			#checksum=zlib.adler32('\00'+fileContent[begin:begin+(row_len)],checksum)
			data+='\00'+fileContent[begin:begin+(row_len)]
			begin+=row_len

		packed=zlib.compress( data,0 )
		idat= ''+struct.pack("!I", len(packed)) +'IDAT'+ packed+ struct.pack("!I", 0xFFFFFFFF & zlib.crc32('IDAT'+packed))
		pngfile.write(idat)

		# fixed: checksums are wrong, but gmp works ####################
		#pngfile.write('\x00\x00\x00\x00')
		#pngfile.write( struct.pack('I',checksum&0xffffffff ))  #data len

		# PNG chunk IEND
		pngfile.write('\x00\x00\x00\x00\x49\x45\x4e\x44\xae\x42\x60\x82')

		pngfile.close()
		os.utime(filename+".png", (mtime, mtime))  # Set access/modified times to now
	elif fileContent[start:start+3] == "BMd" and palette_len >= 16:
		print("RAW image indexed with unknown format - Convertion still unsupported")
	elif fileContent[start:start+2] == "BM" and ord(fileContent[start+2:start+3]) == 8:
		print("RAW image format RGB565")
		checksum=0
		pngfile =open(filename+".png","wb")
		# PNG header
		png_header = [ 0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a ]
		pngfile.write(''.join(map(chr,png_header)))
		# PNG chunk iHDR 
		iHDR_len =  [ 0x00, 0x00, 0x00, 0x0d]
		iHDR_chunk = [ 0x49, 0x48, 0x44, 0x52, 0x00, 0x00, 0x00, int(width), \
				0x00, 0x00, 0x00,  int(height), int(depth/2), 0x02, 0,0,0 ]
		iHDR_crc=zlib.crc32(''.join(map(chr,iHDR_chunk)))
		pngfile.write(''.join(chr(i) for i in iHDR_len))
		pngfile.write(''.join(chr(i) for i in iHDR_chunk))
		iHDR_str= struct.pack('>i',iHDR_crc)
		pngfile.write(iHDR_str)
		# PNG chunk sRGB
		sRGB_chunk= '\x00\x00\x00\x01\x73\x52\x47\x42\x00\xae\xce\x1c\xe9'
		pngfile.write(sRGB_chunk)

		row_len=int( width*depth/8.0 +.99)

		png_colors=pow(2,depth)


		begin=start+16

		data=''
		for row in range (0,height):
			data+='\00'
			for c in range(row_len/2):
				p= ord(fileContent[begin+c*2:begin+c*2+1])
				p+= ord(fileContent[begin+c*2+1:begin+c*2+2]) * 0x100
#				print ("%04x" % p)
				r = p >> 11
				g = (p >> 5) & 0x3f
				b = p & 0x1f
				r = int(round( (r * 255) / 31.0 ))
				g = int(round( (g * 255) / 63.0 ))
				b = int(round( (b * 255) / 31.0 ))
#				print "%02x %02x %02x" % (r,g,b)
				#data+='\00'+chr(r & 0xff)+chr(r>>8)+chr(g&0xff)+chr(g>>8)+chr(b & 0xff)+chr(b>>8)
				data+=chr(r)+chr(g)+chr(b)
			begin+=row_len

		packed=zlib.compress( data,0 )
		idat= ''+struct.pack("!I", len(packed)) +'IDAT'+ packed+ struct.pack("!I", 0xFFFFFFFF & zlib.crc32('IDAT'+packed))
		pngfile.write(idat)

		# PNG chunk IEND
		pngfile.write('\x00\x00\x00\x00\x49\x45\x4e\x44\xae\x42\x60\x82')

		pngfile.close()
		os.utime(filename+".png", (mtime, mtime))  # Set access/modified times to now
	elif fileContent[start:start+2] == "BM" and ord(fileContent[start+2:start+3]) == 27:
		print("RAW image format RGB")
		checksum=0
		pngfile =open(filename+".png","wb")
		# PNG header
		png_header = [ 0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a ]
		pngfile.write(''.join(map(chr,png_header)))
		# PNG chunk iHDR 
		iHDR_len =  [ 0x00, 0x00, 0x00, 0x0d]
		iHDR_chunk = [ 0x49, 0x48, 0x44, 0x52, 0x00, 0x00, 0x00, int(width), \
				0x00, 0x00, 0x00,  int(height), int(depth/3), 0x02, 0,0,0 ]
		iHDR_crc=zlib.crc32(''.join(map(chr,iHDR_chunk)))
		pngfile.write(''.join(chr(i) for i in iHDR_len))
		pngfile.write(''.join(chr(i) for i in iHDR_chunk))
		iHDR_str= struct.pack('>i',iHDR_crc)
		pngfile.write(iHDR_str)
		# PNG chunk sRGB
		sRGB_chunk= '\x00\x00\x00\x01\x73\x52\x47\x42\x00\xae\xce\x1c\xe9'
		pngfile.write(sRGB_chunk)

		row_len=int( width*depth/8.0 +.99)

		png_colors=pow(2,depth)


		begin=start+16

		data=''
		for row in range (0,height):
			#pngfile.write        ('\00'+fileContent[begin:begin+(row_len)])
			#checksum=zlib.adler32('\00'+fileContent[begin:begin+(row_len)],checksum)
			data+='\00'+fileContent[begin:begin+(row_len)]
			begin+=row_len

		packed=zlib.compress( data,0 )
		idat= ''+struct.pack("!I", len(packed)) +'IDAT'+ packed+ struct.pack("!I", 0xFFFFFFFF & zlib.crc32('IDAT'+packed))
		pngfile.write(idat)

		# PNG chunk IEND
		pngfile.write('\x00\x00\x00\x00\x49\x45\x4e\x44\xae\x42\x60\x82')

		pngfile.close()
		os.utime(filename+".png", (mtime, mtime))  # Set access/modified times to now
	else:
		print("RAW image format unknown 0x%02x" % ord(fileContent[start+2:start+3]))

		# set source and target image to same timestamp. 
		# we will use timestamp reading later
	try:
		#os.utime(fname, None)  # Set access/modified times to now
		os.utime(filename+".raw", (mtime, mtime))  # Set access/modified times to now
	except OSError:
		print('File has just been deleted between exists() and utime() calls (or no permission)')

	
mtime = time.mktime(datetime.datetime.now().timetuple())

with open(fileName, mode='rb') as file: # b is important -> binary
	fileContent = file.read()
	#https://docs.python.org/3/library/struct.html#format-strings
	fileHeader = fileContent[0:5]
	version = ord(fileContent[5:6])

	if fileHeader != "HMRES":
		print "file isn't a resource file. Exiting"
		os.exit(1)
	print "file is a Haumi resource file"
	print "version %d" % version

	buf = [ ord(elem) for elem in fileContent[0x10:0x10+4]]
	max_rsrc = (buf[0] <<0) + (buf[1] <<8) + (buf[2] << 16) + (buf[3] <<24)

	print "number of resources: %d" % max_rsrc

#unpack
if args.unpack:

	offs = 4 * max_rsrc + 0x14

	if args.translate:
		#create only translate bitmap
		extract_list = strings_cn.keys()
	else:
		#extract all bitmap and translate the one in the list
		extract_list = range(max_rsrc)

	#extract_list = [ 66, 67, 181, 200, 204, 205]
	for index in extract_list:

		addr = get_rsrc_addr(index)
		print "resource %3d | addr: %x | pos on file: %x" % ( index, addr, offs + addr )

		#sys.stdout.write('.')
		#sys.stdout.flush()

		raw2png(index)

#pack
if args.pack:
	header_res = [ 0x48, 0x4D, 0x52, 0x45, 0x53, version , 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF ]
	#extend the array to make space for number of element and resource's index
	header_res.extend([0]*( 4 + 4 * max_rsrc))
	for i in range(4):
		header_res[0x10 + i] = (max_rsrc >> 8*i) & 0xFF

	offset = 0
	warnings=''
	for index in range(max_rsrc):
		for i in range(4):
			#print (0x14 + index *4 +i), (offset >> 8*i) & 0xFF
			header_res[0x14 + index  * 4+i] = (offset >> 8*i) & 0xFF
		#print "resource %3d | addr: %x " % ( index, offset )
		img,warn = png2raw(index)
	
		header_res.extend(img)
		offset += len(img)
		if warn != '':
			warnings+=warn
	if warnings:
		print "\n\n"+ warnings

	with open(fileName+".new", mode='wb') as output:
		output.write("".join(chr(c) for c in header_res))

		print fileName+".new" + " created"


