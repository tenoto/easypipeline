# -*- coding: utf-8 -*-

import os
import sys 
import yaml 
import glob 
import pandas as pd 
from collections import OrderedDict

import easypipeline.cogamo as cogamo

yaml.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    lambda loader, node: OrderedDict(loader.construct_pairs(node)))

def replace_word_in_file(textfile,old_word,new_word):
	with open(textfile) as reader:
		content = reader.read()
	content = content.replace(old_word,new_word)
	with open(textfile, 'w') as writer:
		writer.write(content)

class PipelineTable(object):
	def __init__(self,name,def_column,def_param,indir,outdir,flag_open=True):
		self.name = name
		self.def_column = def_column
		self.def_param = def_param
		self.indir = indir 
		self.outdir = outdir
		self.flag_open = flag_open
		sys.stdout.write('=== Pipeline: %s generated === \n' % self.name)

		## read def_column and add "--" initial values to the dict object
		self.def_column_yaml = yaml.load(open(self.def_column),Loader=yaml.FullLoader)
		self.cols_dict = OrderedDict()
		for keyword in self.def_column_yaml.keys():
			self.cols_dict[keyword] = []

		self.input_lst = sorted(glob.glob('%s/*.csv' % self.indir,recursive=True))
		for infile in self.input_lst:
			self.cols_dict['Filepath'].append(infile)
			self.cols_dict['Filename'].append(os.path.basename(infile))
			for key in self.cols_dict.keys():
				if key in ('Filename','Filepath'):
					continue
				self.cols_dict[key].append('--')

		## convert the table to the dataframe
		self.df = pd.DataFrame.from_dict(self.cols_dict, orient='index').T

		## prepare the output directory
		if not os.path.exists(self.outdir):
			cmd = 'mkdir -p %s/data' % self.outdir
			print(cmd);os.system(cmd)

		self.table_basename = '%s/%s' % (self.outdir,self.name)
		self.table_csvpath = '%s.csv' % self.table_basename
		self.table_htmlpath = '%s.html'	% self.table_basename
		self.num_of_rows = len(self.df)

	def write(self,overwrite=True):
		if overwrite:
			cmd = 'rm -f %s %s' % (self.table_csvpath,self.table_htmlpath)
			os.system(cmd);#print(cmd);
		self.df.to_csv(self.table_csvpath)
		self.df.to_html(self.table_htmlpath,render_links=True, escape=False)

		replace_word_in_file(self.table_htmlpath,'<td>Done</td>','<td bgcolor="#00CC00">Done</td>')
		replace_word_in_file(self.table_htmlpath,'<td>Error</td>','<td bgcolor="#FF6666">Error</td>')

	def run_pipeline(self,flag_realtime_open=True):
		sys.stdout.write('Pipeline {}: #_of_rows = {}  \n'.format(sys._getframe().f_code.co_name,self.num_of_rows))

		# make initial table 
		self.write() # write the initial table 
		os.system('open %s ' % self.table_htmlpath)

		# start the main loop 
		for index in range(self.num_of_rows):
			#print(self.df.iloc[index])
			sys.stdout.write('-- {}/{} process started.\n'.format(index,self.num_of_rows))

			#### BEGIN: User can modify this ####
			status = '--'
			try:
				cgmhkfile = cogamo.HKData(self.df.iloc[index]['Filepath'])
				cgmhkfile.run(self,index)	
			except Exception as e:
				status = 'Error'
			else:
				status = 'Done'
			finally:
				sys.stdout.write('-- status: {}\n'.format(status))
				self.df.iloc[index]['Status'] = status 
				self.write()
				if flag_realtime_open: os.system('open %s ' % self.table_htmlpath)
			#### END: User can modify this ####				


