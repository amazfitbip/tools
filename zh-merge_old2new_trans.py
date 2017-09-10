#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import sys
import argparse

parser = argparse.ArgumentParser(description='Merge translated strings to new firmware strings')
parser.add_argument('-o', '--output', type=str, dest='output',
					help='file with strings from new firmware', required=True)
parser.add_argument('-i', '--input', type=str, dest='input',
					help='input translated file (old firmware strings)', required=True)

args = parser.parse_args()

old = {}
with open(args.input, 'r') as f:
	# skip version
	f.readline()
	for line in f.readlines():
		addr, hex_, cn, oth = line.split('|')
		old[cn] = oth

new_ = {}
version = ''
with open(args.output, 'r') as f:
	version = f.readline()
	for line in f.readlines():
		addr, hex_, cn, lang = line.split('|')
		if cn not in new_:
			new_[cn] = []
		new_[cn].append({
			'addr': addr,
			'hex': hex_,
			'cn': cn,
			'lang': lang
		})

tmp_out_filename = args.output + ".out"
bak_out_filename = args.output + ".bak"
with open(tmp_out_filename, 'w') as f:
	f.write(version)
	for k in new_:
		if k in old:
			for item in new_[k]:
				f.write('%(addr)s|%(hex)s|%(cn)s|' % item + old[k])
		else:
			for item in new_[k]:
				f.write('%(addr)s|%(hex)s|%(cn)s|%(lang)s' % item)

os.rename(args.output, bak_out_filename)
os.rename(tmp_out_filename, args.output)
os.remove(bak_out_filename)
