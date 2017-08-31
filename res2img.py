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


import sys, struct, os, md5, hashlib, argparse, time, datetime, subprocess, re
if len(sys.argv) == 2:
    fileName = sys.argv[1]

parser = argparse.ArgumentParser(description='Auto-translate and patch firmware files')
parser.add_argument('-l', '--language', dest='language', default="en", #choices=["en","it"],.
					help='l (default:%(default)s)' #, required=True
		    )
#parser.add_argument('-o', '--output', type=str, dest='output', help='output name of translation file, default zh-cn2en.txt')
parser.add_argument('-i', '--input', type=str, dest='input', help='input name of resource file (default:%(default)s)', default='Mili_chaohu.res')
parser.add_argument('-a', '--auto_translate', action='store_true', dest='translate', help='auto translate resource file using known dict')

parser.add_argument('-f', '--format', type=str, dest='imgfmt', help='format of img to generate', default='bmp')

parser.add_argument('-u', dest='unpack', action='store_true', help='unrepack the res file')
parser.add_argument('-p', dest='pack', action='store_true', help='repack the res file')

#parser.add_argument('-m', '--manual_translate', action='store_true',dest='manual_translate', help='manually translate input file')
#parser.add_argument('-f', '--fw', dest='firmwareFile', default="Mili_chaohu.fw", help='f (default:%(default)s)')
#parser.add_argument('-v', dest='verbose', action='store_true', help='verbose')
#parser.add_argument('-p', dest='patch', action='store_true', help='patch firmware file. You can patch firmware with auto translated text (-t), or with manually translated text (-m), or with input file only
#parser.add_argument('-a', dest='analyze', action='store_true', help='analyze input file')
#parser.add_argument("--type", default="toto", choices=["toto","titi"],
#                              help = "type (default: %(default)s)")
#parser.set_defaults(language='en', fw='Mili_chaohu.fw')
args = parser.parse_args()

if not (args.pack or args.unpack):
    print "no argument"
    sys.exit(1)

imgfmt=args.imgfmt

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
    186: "Sun",
    187: "Thu",
    188: "Day",

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

def gen_raw(idx):

	raw="%s%s%03d.%s" % (dirName , os.path.sep , idx, "raw")
	img="%s%s%03d.%s" % (dirName , os.path.sep , idx, imgfmt)

	#the png has been edited... recreate the new raw and load in memory
	raw="%s%s%03d.%s" % (dirName , os.path.sep , idx, "raw")

	#print "QUI1",raw,os.path.getmtime(raw)
	#print "QUI1",img,os.path.getmtime(img)

	if os.path.getmtime(raw) != os.path.getmtime(img):
		cmd = "identify -format %%[bit-depth] %s%s%03d.%s" % (dirName, os.path.sep, idx, imgfmt)
		p = subprocess.Popen(cmd.split(" "), stdout=subprocess.PIPE,
						   stderr=subprocess.PIPE)
		depth, err = p.communicate()

		cmd = "identify -format %%[width] %s%s%03d.%s" % (dirName, os.path.sep, idx, imgfmt)
		p = subprocess.Popen(cmd.split(" "), stdout=subprocess.PIPE,
						   stderr=subprocess.PIPE)
		width, err = p.communicate()

		cmd = "identify -format %%[height] %s%s%03d.%s" % (dirName, os.path.sep, idx, imgfmt)
		p = subprocess.Popen(cmd.split(" "), stdout=subprocess.PIPE,
						   stderr=subprocess.PIPE)
		height, err = p.communicate()

		cmd = "convert %s%s%03d.%s -depth %d -format %%c histogram:info:-" %  (dirName, os.path.sep, idx, imgfmt, int(depth))
		p = subprocess.Popen(cmd.split(" "), stdout=subprocess.PIPE,
						   stderr=subprocess.PIPE)
		out, err = p.communicate()

		palette = []

		for line in out.split("\n"):
			try:
			    #print "PALETTE=",line
			    m = re.match(r".+?(\d+)\,\s*(\d+),\s*(\d+)?.+", line)
			    palette.extend( [ int(m.groups()[0]),int(m.groups()[1]),int(m.groups()[2],0), 0])
			except:
			    pass
		#print "idx =" + str(idx)+" PALETTE=",palette

		stride=int(int(width) * int(depth) / 8) + ((int(width) * int(depth) )% 8 > 0)
		header_bmp = [ 0x42, 0x4D, 0x64, 0x00, int(width), 0x00, int(height) , 0x00, stride, 0x00, int(depth) , 0x00, len(palette) /4, 0 ,0 ,0 ]
		#print header_bmp
		header_bmp.extend(palette)
		#print header_bmp

		#os.system(cmd)
		with open(raw, mode='wb') as rawnew:
			rawnew.write("".join(chr(e) for e in header_bmp))
			rawnew.close()
	    
		cmd = "convert -size "+str(width)+"x"+str(height)+"+"+str(16 + len(palette) * 4) +" -depth " + str(depth) + " +antialias -alpha off " + img + " -compress NONE gray:- >>"+raw
		#print "DEBUG: %s" % cmd
		os.system(cmd)

	else:
		pass

	with open(raw, mode='rb') as rawimg:
		img = [ord(c) for c in rawimg.read()]

	return img


def get_bmp(idx):

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
	#filename = "%03d_%s_%s.bmp" % (idx, m.hexdigest(), ver)

	#I don't know yet what is this bit
	unk = ord(fileContent[start+8:start+9])

	width = ord(fileContent[start+4:start+5])
	height = ord(fileContent[start+6:start+7])

	depth = ord(fileContent[start+0xa:start+0xb])

	print "idx: %d - depth %d bpp - w: %d - h: %d - ??? %d " % (idx, depth, width, height, unk)

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
		cmd = "convert -depth " + str(depth) + " -alpha off -compress NONE -background black -fill white -font DejaVu-Sans -gravity center -pointsize 9 -size "+str(width)+"x"+str(height)+"  label:\"" + string + "\" " +filename+"." + imgfmt +" 2>/dev/null"
		os.system(cmd)
		os.utime(filename+"." + imgfmt, (mtime+60, mtime+60))  # Set access/modified times in the future 
	else:
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

		cmd = "convert -size "+str(width)+"x"+str(height)+"+"+str(16 + palette_len * 4) +" -depth " + str(depth) + " +antialias -alpha off -compress NONE gray:"+filename+".raw "+filename+"clut.png -clut "
		if imgfmt == 'bmp':
		    cmd += " -type palette BMP3:"
		cmd +=filename+"." + imgfmt
		print "DEBUG: %s" % cmd
		os.system(cmd)

		#print "DEBUG: removing "+filename+".pal"
		os.unlink(filename+"clut.png")
		os.utime(filename+"." + imgfmt, (mtime, mtime))  # Set access/modified times to now
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
	fileHeader, version, dummy1, dummmy2 = struct.unpack('5sbHL', fileContent[0:16]) 
	if fileHeader != "HMRES":
	    print "file isn't a resource file. Exiting"
	    os.exit(1)
	print "file is a Haumi resource file"
	print "version??? %d" % version

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

	for index in extract_list:

	    addr = get_rsrc_addr(index)
	    print "resource %3d | addr: %x | pos on file: %x" % ( index, addr, offs + addr )

	    #sys.stdout.write('.')
	    #sys.stdout.flush()
	    get_bmp(index)

#pack
if args.pack:
    header_res = [ 0x48, 0x4D, 0x52, 0x45, 0x53, version , 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF ]
    #extend the array to make space for number of element and resource's index
    header_res.extend([0]*( 4 + 4 * max_rsrc))
    for i in range(4):
        header_res[0x10 + i] = (max_rsrc >> 8*i) & 0xFF

    offset = 0
    for index in range(max_rsrc):
	for i in range(4):
	    #print (0x14 + index *4 +i), (offset >> 8*i) & 0xFF
	    header_res[0x14 + index  * 4+i] = (offset >> 8*i) & 0xFF
	img = gen_raw(index)
	header_res.extend(img)
	offset += len(img)

    with open(fileName+".new", mode='wb') as output:
        output.write("".join(chr(c) for c in header_res))

    print fileName+".new" + " created"

