#!/usr/bin/env python

import argparse

import easypipeline.pipeline as pipeline

__author__ = 'Teruaki Enoto'
__version__ = '0.01'

def get_parser():
	parser = argparse.ArgumentParser(
		prog="run_pipeline.py",
		usage='%(prog)s -c column -p param -i inputdir -o outdir',
		description="""
Run pipeline process. 
"""	)
	version = '%(prog)s ' + __version__
	parser.add_argument('--name', '-n', type=str, required=True, 
		help='pipeline name as used for the summay table')		
	parser.add_argument('--column', '-c', type=str, required=True, 
		help='column name definition yamlfile path')		
	parser.add_argument('--param', '-p', type=str, required=True, 
		help='input parameter yamlfile path')
	parser.add_argument('--indir', '-i', type=str, required=True, 
		help='input file directory path')
	parser.add_argument('--outdir', '-o', type=str, required=True, 
		help='output file directory path')
	return parser

def main(args=None):
	parser = get_parser()
	args = parser.parse_args(args) # get arguments 

	pipe = pipeline.PipelineTable(args.name,args.column,args.param,args.indir,args.outdir)
	pipe.run_pipeline()

if __name__=="__main__":
	main()