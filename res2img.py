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

parser.add_argument('-f', '--format', type=str, dest='imgfmt', help='format of img to generate', choices=["png","bmp"], default='png')

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

def gen_raw(idx):

	raw="%s%s%03d.%s" % (dirName , os.path.sep , idx, "raw")
	img="%s%s%03d.%s" % (dirName , os.path.sep , idx, imgfmt)

	#the png has been edited... recreate the new raw and load in memory
	raw="%s%s%03d.%s" % (dirName , os.path.sep , idx, "raw")

	#print "QUI1",raw,os.path.getmtime(raw)
	#print "QUI1",img,os.path.getmtime(img)

	if os.path.getmtime(raw) != os.path.getmtime(img):
		if args.imgfmt == "bmp":
		    cmd = "identify -format %%[bit-depth] %s%s%03d.%s" % (dirName, os.path.sep, idx, imgfmt)
		else:
		    cmd = "identify -format %%[png:IHDR.bit_depth] %s%s%03d.%s" % (dirName, os.path.sep, idx, imgfmt)
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

		transparency=0
		for line in out.split("\n"):
			try:
			    print "PALETTE=",line
			    m = re.match(r".+?(\d+)\,\s*(\d+),\s*(\d+),*\s*(\d*).+", line)
			    palette.extend( [ int(m.groups()[0]),int(m.groups()[1]),int(m.groups()[2],0), 0])
			    if m.groups()[3] == "0":
				transparency=1
			except Exception as e:
			    #print e
			    pass
		#print "idx =" + str(idx)+" PALETTE=",palette

		#if transparency == 1:
		#    depth=str(int(depth)/8)
		stride=int(int(width) * int(depth) / 8) + ((int(width) * int(depth) )% 8 > 0)

		header_bmp = [ 0x42, 0x4D, 0x64, 0x00, int(width), 0x00, int(height) , 0x00, stride, 0x00, int(depth) , 0x00, len(palette) /4, 0 ,transparency ,0 ]
		#print ["%2x" % c for c in header_bmp]
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

	width = ord(fileContent[start+4:start+5])
	height = ord(fileContent[start+6:start+7])
	stride = ord(fileContent[start+8:start+9])
	depth = ord(fileContent[start+0xa:start+0xb])
	palette_len = ord(fileContent[start+0xc:start+0xd])
	transparency = ord(fileContent[start+0xe:start+0xf])

	print "idx: %3d - depth %2d bpp - w: %3d - h: %3d - stride %3d - transparency %d" % (idx, depth, width, height, stride, transparency)

	filename = dirName +  os.path.sep + "%03d" % (idx)
	#print "DEBUG: palette_len=%d" % palette_len

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
		
		palette = []
		for i in range(palette_len):
		    #print "i: %x" %(16 + i)
		    r=ord(fileContent[start+16+ ( 4*i+0):start+16+ ( 4*i+1)])
		    g=ord(fileContent[start+16+ ( 4*i+1):start+16+ ( 4*i+2)])
		    b=ord(fileContent[start+16+ ( 4*i+2):start+16+ ( 4*i+3)])
		    a=ord(fileContent[start+16+ ( 4*i+3):start+16+ ( 4*i+4)])
		    #print "DEBUG: palette rgb(%3x,%3x,%3x)" %(r,g,b)
		    if a != 0:
			print "DEBUG: alpha(%d)" %a
		    palette.append( [ r,g,b, 0])

		cmd = "convert -alpha off +antialias -compress NONE -size "+str(width)+"x"+str(height)+"+"+str(16 + palette_len * 4)+" -depth %d gray:%s%s%03d.%s -format %%c histogram:info:-" %  (int(depth), dirName, os.path.sep, idx, "raw" )
		p = subprocess.Popen(cmd.split(" "), stdout=subprocess.PIPE,
						   stderr=subprocess.PIPE)
		out, err = p.communicate()
		#print cmd

		colormap = []
		for line in out.split("\n"):
			try:
			    #print "colormap=",line
			    m = re.match(r".+?(\d+)\,\s*(\d+),\s*(\d+)?.+", line)
			    colormap.append( [ int(m.groups()[0]),int(m.groups()[1]),int(m.groups()[2],0), 0])
			    #print "DEBUG: colormap rgb(%3x,%3x,%3x)" %(int(m.groups()[0]),int(m.groups()[1]),int(m.groups()[2],0))
			except:
			    pass
		#print "idx =" + str(idx)+" colormap=",colormap
		#print "DEBUG: colormap_len=%d" % len(colormap)

		#tmpA = mapcolor.mpc
		cmd = "convert -quiet -size %dx%d+%d -depth %d +antialias -compress NONE gray:%s.raw +repage %s.mpc" % (width,height,16 + palette_len * 4,depth,filename, filename)
		#print "DEBUG:", cmd
		os.system(cmd)
		#ww=`convert $tmpA -ping -format "%w" info:`
		#hh=`convert $tmpA -ping -format "%h" info:`
		cmd = "convert -size %dx%d xc:none %s.miff" % (width,height,filename)
		#print "DEBUG:", cmd
		os.system(cmd)

		#cmd = "convert -verbose -channel rgba -alpha on "
		for i in range(palette_len):
		    try:
		#	print "convert '(' ./mapcolors_22153.mpc -channel rgba -alpha on -fill none +opaque 'rgb(0,0,0)' -fill 'rgb(255,255,255)' -opaque 'rgb(0,0,0)' ')' ./mapcolors_0_22153.miff -composite ./mapcolors_0_22153.miff"
			cmd2 = "convert \( %s.mpc -channel rgba -alpha on -fill none +opaque %s -fill %s -opaque %s \) %s.miff -composite %s.miff" %(filename, 
			    "rgb\(%d,%d,%d\)" % (colormap[i][0],colormap[i][1],colormap[i][2]),
			    "rgb\(%d,%d,%d\)" % (palette[i][0],palette[i][1],palette[i][2]),
			    "rgb\(%d,%d,%d\)" % (colormap[i][0],colormap[i][1],colormap[i][2]), filename,filename)
			#print "DEBUG: %s" % cmd2
			os.system(cmd2)
		#	cmd += " -fill rgb\(%d,%d,%d\) -opaque rgb\(%d,%d,%d\)" % (palette[i][0],palette[i][1],palette[i][2], colormap[i][0],colormap[i][1],colormap[i][2], )
			#convert \( $tmpA -channel rgba -alpha on \
			#-fill none +opaque "$color1" \
			#-fill "$color2" -opaque "$color1" \) $tmp0 \
			#-composite $tmp0
		    except Exception as e:
			#print e
			pass

		#cmd += " -size "+str(width)+"x"+str(height)+"+"+str(16 + palette_len * 4) +" -depth " + str(depth) + " +antialias -compress NONE gray:"+filename+".raw "
		#if imgfmt == 'bmp':
		#    cmd += " -type palette BMP3:"
		#cmd +=filename+"." + imgfmt
		#print "DEBUG: %s" % cmd
		#os.system(cmd)

		cmd2 = "convert %s.mpc %s.miff -composite -depth %d " %(filename,filename, depth)
		if transparency == 1:
		    cmd2 += "-transparent rgb\(%d,%d,%d\) " % (palette[0][0],palette[0][1],palette[0][2])

		if imgfmt == 'bmp':
		    cmd2 += " -type palette BMP3:"
		cmd2 +=filename+"." + imgfmt
		#print "DEBUG: %s" % cmd2
		os.system(cmd2)

		os.unlink(filename+".cache")
		os.unlink(filename+".miff")
		os.unlink(filename+".mpc")

		os.utime(filename+"." + imgfmt, (mtime, mtime))  # Set access/modified times to now
	# set source and target image to same timestamp. 
	# we will use timestamp reading later
	try:
	    #os.utime(fname, None)  # Set access/modified times to now
	    os.utime(filename+".raw", (mtime, mtime))  # Set access/modified times to now
	except OSError:
	    print('File has just been deleted between exists() and utime() calls (or no permission)')

	
def png2raw(idx):
   #number of resources: 403
   #resource   0 | addr: 0 | pos on file: 660
   #idx: 0 - depth 2 bpp - w: 84 - h: 84 - ??? 21 
   #DEBUG: rgb(255,0,0)
   #DEBUG: convert -size 84x84+28 -depth 2 +antialias -alpha off -compress NONE gray:_Mili_chao
   #hu.res/000.raw _Mili_chaohu.res/000clut.png -clut  -type palette BMP3:_Mili_chaohu.res/000.

   print "INDEX "+str(idx)
   #imgfmt="png"

   raw="%s%s%03d.%s" % (dirName , os.path.sep , idx, "raw")
   img="%s%s%03d.%s" % (dirName , os.path.sep , idx, imgfmt)

   #the png has been edited... recreate the new raw and load in memory
   raw="%s%s%03d.%s" % (dirName , os.path.sep , idx, "raw")

   #print "QUI1",raw,os.path.getmtime(raw)
   #print "QUI1",img,os.path.getmtime(img)

   if os.path.getmtime(raw) != os.path.getmtime(img):

      start=-4
      palette= []
      size=0
      chunk=""
      transp=0
      remain=-1

      with open(img, mode='rb') as fileRead: # b is important -> binary
         fileContent = fileRead.read()
         #fileHeader, version, dummy1, dummmy2 = struct.unpack('8S    5sbHL', fileContent[0:8])
         fileHeader = struct.unpack('8s', fileContent[0:8])
         png_header = [ 0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a ]

         pippo= (''.join(chr(l) for l in png_header))

         if fileContent[0:8] != (''.join(chr(l) for l in png_header)):
	    print "ERROR: %d isn't a png resource" % idx
            return 1

         rawnew=open(raw, mode='wb')

         #while chunk != "IDAT":
         while chunk != "IEND":
            start+=(12+size)
            print 'startChunk '+str(start)+' chunk: '+str(chunk)+' size '+str(size)
            #temp=struct.unpack('8s', fileContent[start:start+8])
            print 1
            print ":".join("{:02x}".format(ord(c)) for c in (fileContent[start:start+8]))
            #print (fileContent[start:start+8])
            print 2
            size,chunk = struct.unpack('>i4s', fileContent[start:start+8])
            #print size,chunk
            # PNG chunk type IHDR
            if chunk=="IHDR":
               width, height, depth, color, comp, filt, inter = \
                     struct.unpack('>iibbbbb', fileContent[start+8:start+8+size])
               row_len=int( width*depth/8.0 +.99)
               png_colors=pow(2,depth)
               #print "rowlen "+str(row_len)+" colors: "+str(png_colors)
               if (color, comp, filt, inter) != (3,0,0,0) :
                  print "ERROR: %d isn't indexed or uncompressed" % idx
                  return 1
            # PNG chunk type sRGB
            #if chunk=="sRGB":
            # PNG chunk type PLTE .. palette
            if chunk=="PLTE":
               for color in range(0, (size/3) ):
                  r, g, b= struct.unpack('BBB', fileContent[start+8+color*3:start+8+color*3+3])
                  palette.extend( (r, g, b, 0) )
                  #print palette
                  #print palette
                  #print len(palette)
               print 'palette'
               print palette[0:3]
               if palette[0:3]==[254, 254, 0]:
                  #if first colormap entry is 254 254 0 => we consider it as transparent
                  palette[0:3]=[254, 254, 0]
                  transp=1

               stride=int(int(width) * int(depth) / 8) + ((int(width) * int(depth) )% 8 > 0)
               #print "1"
               header_bmp = [ 0x42, 0x4D, 0x64, 0x00, int(width), 0x00, int(height) , 0x00,
                     stride, 0x00, int(depth) , 0x00, len(palette) /4, 0,int(transp), 0 ]
               #print "2"
               header_bmp.extend(palette)
               rawnew.write("".join(chr(e) for e in header_bmp))

            # PNG chunk type IDAT 
            if chunk=="IDAT":

               cursor=0
               if remain ==-1: #first idat
                  cursor+=7 #28 1 1 +  2+2 check
                  remain=0

               #for row_num in range(0, height):
               while  cursor  < size :
                  #pngfile.write('\00')
                  print cursor
                  print  row_len
                  #rawnew.write(fileContent[start:start+(row_len)])
                  if palette[0:3]==[254, 254, 0]:
                  #if first colormap entry is 254 254 0 => we consider it as transparent
                  palette[0:3]=[254, 254, 0]
                  transp=1

               stride=int(int(width) * int(depth) / 8) + ((int(width) * int(depth) )% 8 > 0)
               #print "1"
               header_bmp = [ 0x42, 0x4D, 0x64, 0x00, int(width), 0x00, int(height) , 0x00,
                     stride, 0x00, int(depth) , 0x00, len(palette) /4, 0,int(transp), 0 ]
               #print "2"
               header_bmp.extend(palette)
               rawnew.write("".join(chr(e) for e in header_bmp))

            # PNG chunk type IDAT 
            if chunk=="IDAT":

               cursor=0
               if remain ==-1: #first idat
                  cursor+=7 #28 1 1 +  2+2 check
                  remain=0

               #for row_num in range(0, height):
               while  cursor  < size :
                  #pngfile.write('\00')
                  print cursor
                  print  row_len
                  #rawnew.write(fileContent[start:start+(row_len)])
                  if remain==0:
                     if ord(fileContent[8+start+cursor]) == 0:
                        cursor+=1
                     else:
                        cursor+=4
                     remain=row_len
                  if ( size - cursor) >= remain:
                     write_len=remain
                     remain=0
                  else:
                     write_len=size - cursor
                     remain-=write_len
                  rawnew.write(fileContent[8+start+cursor:8+start+cursor+write_len])
if remain==0:
                     if ord(fileContent[8+start+cursor]) == 0:
                        cursor+=1
                     else:
                        cursor+=4
                     remain=row_len
                  if ( size - cursor) >= remain:
                     write_len=remain
                     remain=0
                  else:
                     write_len=size - cursor
                     remain-=write_len
                  rawnew.write(fileContent[8+start+cursor:8+start+cursor+write_len])
                   cursor+=write_len
               print cursor; size

               #rawnew.close()

               #print "DEBUG: %s" % cmd

         else:
               pass

         rawnew.close()

   with open(raw, mode='rb') as rawimg:
      img = [ord(c) for c in rawimg.read()]

   return img


def raw2png(idx):
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
      cmd = "convert -depth " + str(depth) + " -alpha off -compress NONE -background black -fill white -font DejaVu-Sans -gravity center -pointsize 9 -size "+str(width)+"x"+str(height)+"  label:\"" + string + "\" " +filename+"." + imgfmt +" 2>/dev/null"
      os.system(cmd)
      os.utime(filename+"." + imgfmt, (mtime+60, mtime+60))  # Set access/modified times in the future 
   else:
      checksum=0
      pngfile =open(filename+".png","w")
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
         #print "i: %x" %(16 + i)
         r=ord(fileContent[start+16+ ( 4*i+0):start+16+ ( 4*i+1)])
         g=ord(fileContent[start+16+ ( 4*i+1):start+16+ ( 4*i+2)])
         b=ord(fileContent[start+16+ ( 4*i+2):start+16+ ( 4*i+3)])
         a=ord(fileContent[start+16+ ( 4*i+3):start+16+ ( 4*i+4)])
         print "DEBUG: rgb(%d,%d,%d)" %(r,g,b)
         #palette.extend( (r,g,b) )
         PLTE_chunk+=chr(r)+chr(g)+chr(b)
         if a != 0:
            print "DEBUG: alpha(%d)" %a

      if transp==1:
         #PLTE_chunk[0:3]='\0xfe\0xfe\0x00'
         PLTE_chunk='\0xfe\0xfe\0x00'+PLTE_chunk[3:]

      PLTE_len='\x00\x00\x00'+chr(len(PLTE_chunk))
      PLTE_chunk="PLTE"+ PLTE_chunk

      # write palette
      pngfile.write(PLTE_len)
      pngfile.write(PLTE_chunk)
      PLTE_crc=zlib.crc32(PLTE_chunk)
      PLTE_str= struct.pack('>i',PLTE_crc)
      pngfile.write(PLTE_str)
      #start data
      # PNG chunk IDAT
      pngfile.write( struct.pack('>i',(row_len+1)*height+11))  #data len
      #pngfile.write('\x49\x44\x41\x54\x48\x0d\x01')#\x1c\x0e\xe3\xf1')
      #pngfile.write('IDAT\x78\x01\x00')#\x1c\x0e\xe3\xf1')
      pngfile.write('IDAT\x28\x15\x01')#\x1c\x0e\xe3\xf1')

      pngfile.write( struct.pack('<H',(row_len+1)*height))  #data len
      pngfile.write( struct.pack('<H',65535-(row_len+1)*height))  #data len

      begin=start+16+ ( palette_len * 4)

      #print "rowlen "+str(row_len)+" colors: "+str(png_colors)
      #while begin < end:
      for row in range (0,height):
         #print "begin "+str(begin)
         #pngfile.write('\00')
         #pngfile.write(fileContent[begin:begin+(row_len)])
         pngfile.write        ('\00'+fileContent[begin:begin+(row_len)])
         checksum=zlib.adler32('\00'+fileContent[begin:begin+(row_len)],checksum)
         begin+=row_len

      #pngfile.write('\x7a\xf2\xc5\xf6\xe6\x27\x9f\xdc\x00\x00\x00\x00\x49\x45\x4e\x44\xae\x42\x60\x82')
      #pngfile.write('\x7a\xf2\xc5\xf6\xe6\x27\x9f\xdc')
      pngfile.write( struct.pack('I',checksum&0xffffffff ))  #data len
      pngfile.write('\xe6\x27\x9f\xdc')
      # PNG chunk IEND
      pngfile.write('\x00\x00\x00\x00\x49\x45\x4e\x44\xae\x42\x60\x82')

      #print "DEBUG: %s" % cmd
      #print "DEBUG: removing "+filename+".pal"
      #os.unlink(filename+".pal")

      #print "DEBUG: removing "+filename+".pal"
      #os.unlink(filename+"clut.png")
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
	fileHeader = fileContent[0:5]
	version = ord(fileContent[6:7])

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

	#just for me... comment out to extract all
            if imgfmt=="png":
               raw2png(index)
            else:
	       get_bmp(index)

	#just for me... uncomment to extract just an image
	#get_bmp(127)
	#get_bmp(181)

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
        if imgfmt=="png":
           img = png2raw(index)
        else:	
           img = gen_raw(index)
	
	header_res.extend(img)
	offset += len(img)

    with open(fileName+".new", mode='wb') as output:
        output.write("".join(chr(c) for c in header_res))

    print fileName+".new" + " created"

