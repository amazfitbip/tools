#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Simple python command line tool to pack / unpack the Amazfit Bip font firmware files

# (C) José Rebelo
# https://gist.github.com/joserebelo/b9be41b7b88774f712e2f864fdd39878

# (E) Yener Durak & Eddie - Make this working with Amazfit Bip
# https://gist.github.com/joserebelo/b9be41b7b88774f712e2f864fdd39878

# Thanks to https://github.com/prof-membrane for initial analisys
# https://github.com/Freeyourgadget/Gadgetbridge/issues/734#issuecomment-320108514

from PIL import Image
from pathlib import Path
import math
import binascii
import sys
import os
import glob

# Unpack the Amazfit Bip font file
# Creates 1bpp bmp images
def unpackFont(font_path):
	print('Unpacking', font_path)
	
	font_file = open(font_path, 'rb')
	font_path.join(font_path.split(os.sep)[:-1])
	if not os.path.exists('bmp'):
		os.makedirs('bmp')
	# header = 16 bytes
	header = font_file.read(0x22)
	num_ranges = (header[0x21] << 8) + header[0x20]
	
	ranges = font_file.read(num_ranges*6)
	startrange = (ranges[len(ranges)-5] << 8) + ranges[len(ranges)-6]
	endrange = (ranges[len(ranges)-3] << 8) + ranges[len(ranges)-4]
	num_characters = (ranges[len(ranges)-1] << 8) + ranges[len(ranges)-2] +  endrange - startrange + 1

	startrange = (ranges[1] << 8) + ranges[0]
	endrange = (ranges[3] << 8) + ranges[2]
	range_nr = 0;
	for i in range (0, num_characters):

		img = Image.new('1', (16, 16), 0)
		pixels = img.load()
		char_bytes = font_file.read(32)
		
		x = 0
		y = 0
		# big endian
		for byte in char_bytes:
			#print (byte)
			bits = [(byte >> bit) & 1 for bit in range(8 - 1, -1, -1)]
			for b in bits:
				pixels[x, y] = b
				x += 1
				if x == 16:
					x = 0
					y += 1
		margin_top = font_file.read(1)
		img.save("bmp" + os.sep + '{:04x}'.format(startrange) + str(margin_top[0] % 16) + '.bmp') 
		
		startrange += 1
		if startrange > endrange and range_nr+1 < num_ranges:
			range_nr += 1
			startrange = (ranges[range_nr * 6 + 1] << 8) + ranges[range_nr * 6]
			endrange = (ranges[range_nr * 6 + 3] << 8) + ranges[range_nr * 6 + 2]

# Create a Amazfit Bip file from bmps
def packFont(font_path):
	print('Packing', font_path)
	font_file = open(font_path, 'wb')
	header = bytearray(binascii.unhexlify('4E455A4B08FFFFFFFFFF01000000FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF0000'))
	bmps = bytearray()
	
	range_nr = 0
	seq_nr = 0
	startrange = -1
	
	bmp_files = sorted(glob.glob('bmp' +  os.sep + '*'))

	for i in range (0, len(bmp_files)):
		margin_top = int(bmp_files[i][8])
		
		if(i == 0):
			unicode = int(bmp_files[i][4:-5],16)
		else:
			unicode = next_unicode
		
		if(i+1 < len(bmp_files)):
			next_unicode = int(bmp_files[i+1][4:-5],16)
		else:
			next_unicode = -1
		
		if (unicode != next_unicode):		
			if (startrange == -1):
				range_nr += 1			 
				startrange = unicode
			
			img = Image.open(bmp_files[i])
			img_rgb = img.convert('RGB')
			pixels = img_rgb.load()

			x = 0
			y = 0
			char_width = 0;

			while y < 16:
				b = 0
				for j in range(0, 8):
					if pixels[x, y] != (0, 0, 0):
						b = b | (1 << (7 - j))
						if (x > char_width):
							char_width = x
					x += 1
					if x == 16:
						x = 0
						y += 1
				bmps.extend(b.to_bytes(1, 'big'))
			char_width = char_width * 16 + margin_top;
			bmps.extend(char_width.to_bytes(1, 'big'))
			
			if (unicode+1 != next_unicode):
				endrange = unicode
				sb = startrange.to_bytes(2, byteorder='big')
				header.append(sb[1])
				header.append(sb[0])
				eb = endrange.to_bytes(2, byteorder='big')	
				header.append(eb[1])
				header.append(eb[0])
				seq = seq_nr.to_bytes(2, byteorder='big')	
				header.append(seq[1])
				header.append(seq[0])
				seq_nr += endrange - startrange + 1
				startrange = -1
		else:
			print('multiple files of {:04x}'.format(unicode))

	rnr = range_nr.to_bytes(2, byteorder='big')
	header[0x20] = rnr[1]
	header[0x21] = rnr[0]

	font_file.write(header)	
	font_file.write(bmps)		

if len(sys.argv) == 3 and sys.argv[1] == 'unpack':
	unpackFont(sys.argv[2])
elif len(sys.argv) == 3 and sys.argv[1] == 'pack':
	packFont(sys.argv[2])
else:
	print('Usage:')
	print('   python', sys.argv[0], 'unpack Mili_chaohu.ft')
	print('   python', sys.argv[0], 'pack new_Mili_chaohu.ft')
