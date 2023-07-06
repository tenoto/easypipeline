#!/usr/bin/env python

import argparse

import os 
import sys 
import yaml 
import pandas as pd 
from astropy.table import Table

__author__ = 'Teruaki Enoto'
__version__ = '0.01'

def get_parser():
	parser = argparse.ArgumentParser(
		prog="convert_csv2fits.py",
		usage='%(prog)s csvfile',
		description="""
Convert input csvfile to fitsfile.
"""	)
	parser.add_argument('csvfile',metavar='csvfile',type=str, 
		help='Input csvfile.')
	parser.add_argument('--column', '-c', type=str, required=False, 
		help='column name definition yamlfile path')	
	return parser

def main(args=None):
	parser = get_parser()
	args = parser.parse_args(args) # get arguments 

	if not os.path.exists(args.csvfile):
		raise FileNotFoundError("{} not found".format(args.csvfile))

	try:
		outfitsfile = args.csvfile.replace('.csv','.fits')
		cmd = 'rm -f %s' % outfitsfile
		os.system(cmd)		

		df = pd.read_csv(args.csvfile)
		df = df.rename(columns={'Unnamed: 0': 'index'})	
		table = Table.from_pandas(df)

		if args.column is not None:
			sys.stdout.write('%s\n' % args.column)
			def_column_yaml = yaml.load(open(args.column),Loader=yaml.FullLoader)
			for colname in table.columns:
				if colname == 'index':
					continue 
				table[colname].unit = def_column_yaml[colname]['unit']
				#table.columns[colname].format  = def_column_yaml[colname]['format']
			table.write(outfitsfile)
	except Exception as e:
		sys.stderr.write("[error]\n")
		raise
	else:
		sys.stdout.write("%s is generated.\n" % outfitsfile)

if __name__=="__main__":
	main()

