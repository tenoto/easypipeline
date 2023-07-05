# -*- coding: utf-8 -*-

import os
import sys 
import yaml 
import glob 
import pandas as pd 
from collections import OrderedDict

yaml.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    lambda loader, node: OrderedDict(loader.construct_pairs(node)))

class Pipeline(object):
	def __init__(self,name,def_column,def_param,indir,outdir):
		self.name = name
		self.def_param = def_param
		self.def_column = def_column
		self.indir = indir 
		self.outdir = outdir
		sys.stdout.write('[Pipeline:generated]\n')

		self.cols_dict = yaml.load(open(self.def_column),Loader=yaml.FullLoader)
		self.input_lst = sorted(glob.glob('%s/*.csv' % self.indir,recursive=True))
		for infile in self.input_lst:
			self.cols_dict['filepath'].append(infile)
			self.cols_dict['filename'].append(os.path.basename(infile))
			for key in self.cols_dict.keys():
				if key in ('filename','filepath'):
					continue
				self.cols_dict[key].append('--')

		self.df = pd.DataFrame.from_dict(self.cols_dict, orient='index').T

		if not os.path.exists(self.outdir):
			cmd = 'mkdir -p %s' % self.outdir
			print(cmd);os.system(cmd)

		self.table_basename = '%s/%s' % (self.outdir,self.name)
		self.table_csvpath = '%s.csv'
		self.table_htmlpath = '%s.html'		

	def write_to_table(self):
		cmd = 'rm -f %s %s' % (self.table_csvpath,self.table_htmlpath)
		os.system(cmd);#print(cmd);
		self.df.to_csv(self.table_csvpath)
		self.df.to_html(self.table_htmlpath,render_links=True, escape=False)

	def run(self):
		self.write_to_table()

	def run_task(self):
		sys.stdout.write('[Pipeline] {} \n'.format(sys._getframe().f_code.co_name))
		for index in range(len(self.df)):
			print(index)
			print(self.df.iloc[index])

class Logfile(object):
	def __init__(self,filepath):
		self.filepath = filepath 