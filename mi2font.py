#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Simple python command line tool to pack / unpack the Mi Band 2 font firmware files

# (C) José Rebelo
# https://gist.github.com/joserebelo/b9be41b7b88774f712e2f864fdd39878

# Thanks to https://github.com/prof-membrane for initial analisys
# https://github.com/Freeyourgadget/Gadgetbridge/issues/734#issuecomment-320108514

from PIL import Image
import os
import math
import binascii
import sys

# Unpack the Mi Band 2 font file
# Creates 1bpp bmp and txt file with the characters
def unpackFont(font_path):
    print('Unpacking', font_path)
    font_file = open(font_path, 'rb')
    txt_file = open(font_path + ".txt", 'wb')

    # header = 16 bytes
    header = font_file.read(16)

    # last 2 header bytes = number of bytes used for characters
    # 2 bytes per character, utf-16le
    num_bytes_characters = (header[15] << 8) + header[14]
    num_characters = num_bytes_characters // 2

    # read the characters
    for i in range (0, num_characters):
        b = font_file.read(2)
        txt_file.write(b)

    # spritesheet dimensions (square)
    
    dim = int(math.ceil(math.sqrt(num_characters)))

    img = Image.new('1', (dim * 16, dim * 16), 0)
    pixels = img.load()

    for i in range (0, num_characters):
        # each character is a 16x16 image, 1 bit per pixel, meaning 32 bytes
        char_bytes = font_file.read(32)
        row = i // dim
        col = i % dim
        x = 0
        y = 0
        # big endian
        for byte in char_bytes:
            bits = [(byte >> bit) & 1 for bit in range(8 - 1, -1, -1)]
            for b in bits:
                pixels[16 * col + x, 16 * row + y] = b
                x += 1
                if x == 16:
                    x = 0
                    y += 1

    img.save(font_path + '.bmp')

# Create a Mi Band 2 font file from a bmp and txt
def packFont(bmp_path, txt_path, font_path):
    print('Packing', font_path)

    font_file = open(font_path, 'wb')
    bmp_file = open(bmp_path, 'rb')
    txt_file = open(txt_path, 'rb')

    characters = txt_file.read()
    num_characters = len(characters) // 2

    # sort the characters, keep track of each index
    chars_arr = str(characters, 'utf-16le')
    chars_idx = range(num_characters)
    chars = list(sorted(zip(chars_arr, chars_idx)))

    # header, taken from Mili_pro.ft.en
    header = bytearray(binascii.unhexlify('484D5A4B01FFFFFFFF00FFFFFFFFCA00'))
    # header, taken from Mili_pro.ft
    # header = bytearray(binascii.unhexlify('484D5A4B01FFFFFFFFFFFFFFFFFF7438'))
    l = len(characters).to_bytes(2, byteorder='big')
    header[14] = l[1]
    header[15] = l[0]
    font_file.write(header)

    img = Image.open(bmp_path)
    cols = img.size[0] // 16
    rows = img.size[1] // 16
    img_rgb = img.convert('RGB')
    pixels = img_rgb.load()

    for i in range (0, num_characters):
    	font_file.write(chars[i][0].encode('utf-16le'))

    for i in range (0, num_characters):
        idx = chars[i][1]
        row = idx // cols
        col = idx % cols
        x = 0
        y = 0

        while y < 16:
            b = 0
            for i in range(0, 8):
                if pixels[col * 16 + x, row * 16 + y] != (0, 0, 0):
                    b = b | (1 << (7 - i))

                x += 1
                if x == 16:
                    x = 0
                    y += 1
            font_file.write(b.to_bytes(1, 'big'))

if len(sys.argv) == 3 and sys.argv[1] == 'unpack':
    unpackFont(sys.argv[2])
elif len(sys.argv) == 5 and sys.argv[1] == 'pack':
    packFont(sys.argv[2], sys.argv[3], sys.argv[4])
else:
    print('Usage:')
    print('   python', sys.argv[0], 'unpack Mili_pro.ft.en')
    print('   python', sys.argv[0], 'pack Mili_pro.ft.en.bmp Mili_pro.ft.en.txt out.ft.en')
