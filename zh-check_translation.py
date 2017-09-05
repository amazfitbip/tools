#!/usr/bin/python
# -*- coding: utf-8 -*-

import re
import sys
import argparse

parser = argparse.ArgumentParser(description='Check length of translated strings')
parser.add_argument('-i', '--input', type=str, dest='input',
					help='input name of translated file', required=True)
args = parser.parse_args()

with open(args.input, 'r') as f:
	version = f.readline()
	if not re.match('^#.+:.+$', version):
		print "ERROR: version string doesnt match"
		sys.exit(1)

	error = False
	row_num = 2
	for line in f.readlines():
		sp = line.strip().split('|')
		if len(sp) < 4:
			print "ERROR: %d. line has too few columns (min 4): '%s'" % (row_num, line.strip())
			error = True
		elif len(sp[2]) < len(sp[3]):
			print "ERROR: %d. Translated string is too long (%d > %d)" % (row_num, len(sp[3]), len(sp[2]))
			error = True
		row_num += 1
	if error:
		sys.exit(1)

print "OK!"
