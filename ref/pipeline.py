#!/usr/bin/env python

import os 
import sys 
import glob 
import yaml
import numpy as np 
import pandas as pd 
import matplotlib.pylab as plt 

from iminuit import Minuit
#from probfit import BinnedChi2
from probfit import Chi2Regression


FONTSIZE = 18

##########################
# General functions
##########################

def model_gauss(x, mu, sigma, area):
    return area * np.exp(-0.5*(x-mu)**2/sigma**2)/(np.sqrt(2*np.pi)*sigma)

def model_gauss_continuum(x, mu, sigma, area, c0=0.0, c1=0.0):
    return area * np.exp(-0.5*(x-mu)**2/sigma**2)/(np.sqrt(2*np.pi)*sigma) + c0 + c1 * x 

class Hist1D(object):
	def __init__(self, nbins, xlow, xhigh):
		self.nbins = nbins
		self.xlow  = xlow
		self.xhigh = xhigh
		#print(self.nbins,self.xlow,self.xhigh)
		self.hist, edges = np.histogram([], bins=nbins, range=(xlow, xhigh))
		self.bins = (edges[:-1] + edges[1:]) / 2.
		#print(self.hist,edges,self.bins)

	def fill(self, arr):
		#print(arr)
		hist, edges = np.histogram(arr, bins=self.nbins, range=(self.xlow, self.xhigh))
		self.hist += hist
		self.err = np.sqrt(self.hist)

	@property
	def data(self):
		return self.bins, self.hist

##########################
# Pipeline archive
##########################

class Archive(object):
	def __init__(self,parameter_yamlfile):
		self.param = yaml.load(open(parameter_yamlfile),
			Loader=yaml.FullLoader)		
		print("[Archive] %s is generatd." % self.param['archive_name'])

		self.dict = {
			'detid':[],
			'time':[],
			'process': [],
			'bstcand': [],
			'bstlclink': [],
			'bstlcfile': [],	
			'bstdistlink': [],
			'bstdistfile': [],	
			'bstlc_mean':[],
			'bstlc_sigma':[],
			'bstlc_area':[],	
			'bstalert_link': [],
			'bstalert_file': [],
			'lclink': [],
			'lcfile': [],
			'phalink': [],
			'phafile': [],
			'csvfile':[],
			'csvpath':[],			
			'csvlink':[]
			}

	def set_csvfiles(self):
		sys.stdout.write('[archive] {} \n'.format(sys._getframe().f_code.co_name))

		### Find CSV file and make archives. 
		csv_filelst = sorted(glob.glob('%s/**/*.csv' % self.param['datadir'],
			recursive=True))
		for file_path in csv_filelst:
			self.add(file_path)		

	def add(self,file_path):
		print("[Archive %s] add %s" % (self.param['archive_name'],file_path))

		filename = os.path.basename(file_path)	
		basename, ext = os.path.splitext(filename)
		if ext != '.csv':
			print("Warning: skip the file %s" % csvfile)
			return -1
		detid, yyyymmdd, hour = basename.split("_")
		#print(detid,yyyymmdd,hour)

		year = yyyymmdd[0:4]
		month = yyyymmdd[4:6]
		day = yyyymmdd[6:8]		
		str_time = '%04d-%02d-%02dT%02d:00:00' % (int(year),int(month),int(day),int(hour))

		self.dict['detid'].append(detid)
		self.dict['time'].append(str_time)
		self.dict['process'].append('--')
		self.dict['bstcand'].append('--')
		self.dict['bstlclink'].append('--')
		self.dict['bstlcfile'].append('--')
		self.dict['bstdistlink'].append('--')
		self.dict['bstdistfile'].append('--')
		self.dict['bstlc_mean'].append('--')
		self.dict['bstlc_sigma'].append('--')
		self.dict['bstlc_area'].append('--')				
		self.dict['csvlink'].append('<a href="%s">%s</a>' % (file_path,filename))
		self.dict['csvpath'].append(file_path)		
		self.dict['csvfile'].append(filename)
		self.dict['bstalert_link'].append('--')
		self.dict['bstalert_file'].append('--')
		self.dict['lclink'].append('--')
		self.dict['lcfile'].append('--')			
		self.dict['phalink'].append('--')
		self.dict['phafile'].append('--')		
		return 0 

	def convert_to_dataframe(self):
		self.df = pd.DataFrame.from_dict(self.dict, orient='index').T
		#self.df = self.df.shift()[1:] # shift index starting from 0 to 1	

	def process(self,index):
		print("[Archive %s] process index of %s" % (self.param['archive_name'],index))

		csvpath = self.df.iloc[index]['csvpath']
		evt = EventFile(csvpath)

		outdir = '%s/product/id%s/%s/%s/%s/%s' % (self.param['outdir'],evt.detid, evt.year, evt.month, evt.day, evt.hour)

		# make directory 
		evt.mkdir(outdir)

		# draw spectrum
		pha_spectrum_pdf = evt.plot_pha_spectrum(
			pha_min=self.param['plot_pha_spectrum_min'],
			pha_max=self.param['plot_pha_spectrum_max'],
			pha_nbin=self.param['plot_pha_spectrum_nbin'],
			xmin=self.param['plot_pha_spectrum_xmin'],
			xmax=self.param['plot_pha_spectrum_xmax'])
		self.df.iloc[index]['phalink'] = '<a href=\"../%s\">pha_spec</a>' % (pha_spectrum_pdf)
		self.df.iloc[index]['phafile'] = pha_spectrum_pdf

		# draw light curves 
		energy_sorted_curve_pdf = evt.plot_energy_sorted_curves(
			tbin=self.param['plot_energy_sorted_curves_tbin'],
			tmin=self.param['plot_energy_sorted_curves_tmin'],
			tmax=self.param['plot_energy_sorted_curves_tmax'],
			pha_bands_list=list(self.param['plot_energy_sorted_curves_bands'])
			)
		self.df.iloc[index]['lclink'] = '<a href=\"../%s\">lc</a>' % (energy_sorted_curve_pdf)
		self.df.iloc[index]['lcfile'] = energy_sorted_curve_pdf

		# search burst 
		search_burst_fit_pdf, fit_values, fit_errors, mask_burst_candidates = evt.search_burst(
			tbin=self.param['search_burst_tbin'],
			pha_min=self.param['search_burst_pha_min'],
			pha_max=self.param['search_burst_pha_max'],
			hist_min=self.param['search_burst_hist_min'],
			hist_max=self.param['search_burst_hist_max'],
			hist_nbin=self.param['search_burst_hist_nbin'],
			threshold_sigma=self.param['search_burst_threshold_sigma'])
		bstlc_pdf = evt.plot_curve(
			tbin=self.param['search_burst_tbin'],
			tmin=self.param['plot_energy_sorted_curves_tmin'],
			tmax=self.param['plot_energy_sorted_curves_tmax'],
			pha_min=self.param['search_burst_pha_min'],
			pha_max=self.param['search_burst_pha_max'],
			mask_burst_candidates=mask_burst_candidates)

		self.df.iloc[index]['bstcand'] = sum(mask_burst_candidates)
		self.df.iloc[index]['bstlclink'] = '<a href=\"../%s\">lc_bst</a>' % (bstlc_pdf)
		self.df.iloc[index]['bstlcfile'] = bstlc_pdf
		self.df.iloc[index]['bstdistlink'] = '<a href=\"../%s\">lc_bst</a>' % (search_burst_fit_pdf)
		self.df.iloc[index]['bstdistfile'] = search_burst_fit_pdf

		self.df.iloc[index]['bstlc_mean'] = '%.1f' % fit_values['mu']
		self.df.iloc[index]['bstlc_sigma'] = '%.1f' % fit_values['sigma']
		self.df.iloc[index]['bstlc_area'] = '%.1f' % fit_values['area']			

		bstalert_pdf = evt.burst_alert(
			tbin=self.param['burst_alert_tbin'],
			tmin=self.param['plot_energy_sorted_curves_tmin'],
			tmax=self.param['plot_energy_sorted_curves_tmax'],
			pha_min=self.param['burst_alert_pha_min'],
			pha_max=self.param['burst_alert_pha_max'],
			runave_width=self.param['burst_alert_width'],
			runave_threshold=self.param['burst_alert_threshold'])
		self.df.iloc[index]['bstalert_link'] = '<a href=\"../%s\">alert</a>' % (bstalert_pdf)
		self.df.iloc[index]['bstalert_file'] = bstalert_pdf

		self.df.iloc[index]['process'] = 'DONE'

	def write(self):
		if not os.path.exists(self.param['outdir']):
			cmd = 'mkdir -p %s' % self.param['outdir']
			print(cmd);os.system(cmd)

		cmd = 'rm -f %s/%s.{csv,html}' % (self.param['outdir'],self.param['archive_name'])
		print(cmd);os.system(cmd)
	
		self.df.to_csv('%s/%s.csv' % (self.param['outdir'],self.param['archive_name']))

		self.df.drop(['csvpath','csvfile','lcfile','phafile','bstlcfile','bstdistfile','bstalert_file'],axis=1).to_html('%s/%s.html' % (self.param['outdir'],self.param['archive_name']), render_links=True, escape=False)

class EventFile(object):
	def __init__(self, file_path):
		self.file_path = file_path
		self.basename = os.path.splitext(os.path.basename(self.file_path))[0]

		if not os.path.exists(self.file_path):
			raise FileNotFoundError("{} not found".format(self.file_path))
		try:
			self.df = pd.read_csv('%s' % self.file_path,
				header=None,
				names=['minuite','seconds','100microseconds','pha'])
		except OSError as e:
			raise

		self.format = 'csv'
		self.nevents = len(self.df)		

		self.df['time_sec'] = self.df['minuite'] * 60.0 + self.df['seconds'] + self.df['100microseconds'] * 1/10000

		self.detid, self.yyyymmdd, self.hour = self.basename.split("_")

		self.year = self.yyyymmdd[0:4]
		self.month = self.yyyymmdd[4:6]
		self.day = self.yyyymmdd[6:8]				

	def mkdir(self,outdir):
		sys.stdout.write('----- {} -----\n'.format(sys._getframe().f_code.co_name))

		self.outdir = outdir

		cmd = 'mkdir -p %s' % self.outdir 
		print(cmd);os.system(cmd)

	def plot_pha_spectrum(self,pha_min=0,pha_max=2**10,pha_nbin=2**9,xmin=15,xmax=2**10):
		sys.stdout.write('----- {} -----\n'.format(sys._getframe().f_code.co_name))
	
		outpdf = '%s/%s_pha_spectrum.pdf' % (self.outdir,self.basename)

		#y, xedges, patches = plt.hist(self.df['pha'],
		#	range=(pha_min,pha_max),bins=pha_nbin,histtype='step')
		#x = 0.5*(xedges[1:] + xedges[:-1])

		self.pha_spectrum = Hist1D(nbins=pha_nbin,xlow=pha_min,xhigh=pha_max)
		self.pha_spectrum.fill(self.df['pha'])

		fig, ax = plt.subplots(1,1, figsize=(11.69,8.27))
		plt.errorbar(
			self.pha_spectrum.bins,
			self.pha_spectrum.hist,			
			yerr=self.pha_spectrum.err,
			marker='',drawstyle='steps-mid')

		plt.xlabel('ADC channel (pha)', fontsize=FONTSIZE)
		plt.ylabel('Counts', fontsize=FONTSIZE)
		plt.title(self.basename,fontsize=FONTSIZE)
		plt.xscale('log')				
		plt.yscale('log')
		plt.xlim(xmin,xmax)
		plt.tight_layout(pad=2)
		plt.tick_params(labelsize=FONTSIZE)
		plt.rcParams["font.family"] = "serif"
		plt.rcParams["mathtext.fontset"] = "dejavuserif"		

		ax.minorticks_on()
		ax.grid(True)
		ax.grid(axis='both',which='major', linestyle='--', color='#000000')
		ax.grid(axis='both',which='minor', linestyle='--')	
		ax.tick_params(axis="both", which='major', direction='in', length=5)
		ax.tick_params(axis="both", which='minor', direction='in', length=3)
		plt.savefig(outpdf)
		print(outpdf)
		return outpdf 

	def extract_curve(self,tbin=1.0,tmin=0.0,tmax=3600.,
		pha_min=None,pha_max=None):
		sys.stdout.write('----- {} -----\n'.format(sys._getframe().f_code.co_name))

		if pha_min == 'None':
			pha_min = None
		if pha_max == 'None':
			pha_max = None

		print(pha_min,pha_max)
		if pha_min == None and pha_max == None:
			print("no pha selection.")
			suffix = 'pha_all' 
			mask = np.full(len(self.df), True)
		elif pha_min != None and pha_max == None:
			print("%d <= pha" % pha_min)	
			suffix = 'pha_%d_xx'	% (pha_min)								
			mask = (self.df['pha'] >= pha_min)
		elif pha_min == None and pha_max != None:
			print("pha <= %d" % pha_max)				
			suffix = 'pha_xx_%d' % (pha_max)		
			mask = (self.df['pha'] <= pha_max)
		elif pha_min != None and pha_max != None:
			print("%d <= pha <= %d" % (pha_min,pha_max))
			suffix = 'pha_%d_%d'	% (pha_min,pha_max)			
			mask = np.logical_and((self.df['pha'] >= pha_min),(self.df['pha'] <= pha_max))

		print("%d --> %d (%.2f%%)" % (len(self.df),len(self.df[mask]),
			float(len(self.df[mask]))/float(len(self.df))*100.0))

		nbins = round((tmax-tmin)/tbin)
		hist_lc = Hist1D(nbins, tmin, tmax)
		#print(self.df['TIME'][mask]-self.df['time_sec'][0])
		hist_lc.fill(self.df['time_sec'][mask])
		return hist_lc,suffix

	def plot_energy_sorted_curves(self,tbin=1.0,tmin=0.0,tmax=3600.,
		pha_bands_list=[[None,30],[30,100],[100,300],[300,None]]):
		sys.stdout.write('----- {} -----\n'.format(sys._getframe().f_code.co_name))

		outpdf = '%s/%s_curves.pdf' % (self.outdir,self.basename)

		lchist_list = []
		suffix_list = []
		for pha_bands in pha_bands_list:
			pha_min, pha_max = pha_bands
			if pha_min == 'None':
				pha_min = None
			if pha_max == 'None':
				pha_max = None
			lchist,suffix = self.extract_curve(tbin=tbin,
				tmin=tmin,tmax=tmax,
				pha_min=pha_min,pha_max=pha_max)				
			lchist_list.append(lchist)
			suffix_list.append(suffix)

		fig, axs = plt.subplots(len(pha_bands_list),1, figsize=(8.27,11.69), 
			sharex=True, gridspec_kw={'hspace': 0})
		for i in range(len(pha_bands_list)):
			pha_min,pha_max = pha_bands_list[i]
			label = '%s <= pha <= %s ' % (pha_min,pha_max)
			axs[i].errorbar(
				lchist_list[i].bins,
				lchist_list[i].hist,
				yerr=lchist_list[i].err,
				marker='',drawstyle='steps-mid',
				label=label)
			axs[i].set_xlim(tmin,tmax)
			axs[i].legend()
			if i == 0:
				axs[i].set_title('%s' % (self.basename),fontsize=FONTSIZE)				
			if tbin < 1.0:
				axs[i].set_ylabel('Counts/%d ms' % tbin*1000, fontsize=FONTSIZE)
			else:
				axs[i].set_ylabel('Counts/%d sec' % tbin, fontsize=FONTSIZE)
			if i == len(pha_bands_list)-1:
				axs[i].set_xlabel('Time (sec)', fontsize=FONTSIZE)
		for ax in axs:
			ax.label_outer()	
			ax.minorticks_on()
			ax.xaxis.grid(True)
			ax.xaxis.grid(which='major', linestyle='--', color='#000000')
			ax.xaxis.grid(which='minor', linestyle='-.')	
			ax.tick_params(axis="both", which='major', direction='in', length=5)
			ax.tick_params(axis="both", which='minor', direction='in', length=3)			
		fig.align_ylabels(axs)
		plt.tight_layout(pad=2)
		plt.rcParams["font.family"] = "serif"
		plt.rcParams["mathtext.fontset"] = "dejavuserif"		
		plt.savefig(outpdf)	
		print(outpdf)
		return outpdf 

	def plot_curve(self,tbin=1.0,tmin=0.0,tmax=3600.,
		pha_min=None,pha_max=None,mask_burst_candidates=None):
		sys.stdout.write('----- {} -----\n'.format(sys._getframe().f_code.co_name))

		if pha_min == 'None':
			pha_min = None
		if pha_max == 'None':
			pha_max = None

		lchist,suffix = self.extract_curve(tbin=tbin,tmin=tmin,tmax=tmax,
		pha_min=pha_min,pha_max=pha_max)

		outpdf = '%s/%s_curve_%s.pdf' % (self.outdir,self.basename,suffix)

		fig, ax = plt.subplots(1,1, figsize=(11.69,8.27))		

		plt.errorbar(lchist.bins,lchist.hist,
			yerr=lchist.err,marker='',drawstyle='steps-mid')
		if isinstance(mask_burst_candidates, np.ndarray) and sum(mask_burst_candidates) > 0:
			for x in lchist.bins[mask_burst_candidates]:
				tstart = x - 0.5 * tbin 
				tstop = x + 0.5 * tbin	
				ax.axvspan(tstart, tstop, color="red", alpha=0.3)
			#plt.fill_between(
			#	lchist.bins[mask_burst_candidates],
			#	lchist.hist[mask_burst_candidates])
#			#	marker='',drawstyle='steps-mid',color='red')			

		plt.xlabel('Time (sec)', fontsize=FONTSIZE)
		if tbin < 1.0:
			plt.ylabel('Counts/%d ms' % tbin*1000, fontsize=FONTSIZE)
		else:
			plt.ylabel('Counts/%d sec' % tbin, fontsize=FONTSIZE)
		plt.title('%s (%s ch <= pha <= %s ch)' % (self.basename,pha_min,pha_max),
			fontsize=FONTSIZE)
		#plt.xscale('log')				
		#plt.yscale('log')
		plt.xlim(tmin,tmax)
		plt.tight_layout(pad=2)
		plt.tick_params(labelsize=FONTSIZE)
		plt.rcParams["font.family"] = "serif"
		plt.rcParams["mathtext.fontset"] = "dejavuserif"		

		ax.minorticks_on()
		ax.grid(True)
		ax.grid(axis='both',which='major', linestyle='--', color='#000000')
		ax.grid(axis='both',which='minor', linestyle='--')	
		ax.tick_params(axis="both", which='major', direction='in', length=5)
		ax.tick_params(axis="both", which='minor', direction='in', length=3)
	
		plt.savefig(outpdf)	
		print(outpdf)
		return outpdf 

	def search_burst(self,tbin=16.0,tmin=0.0,tmax=3600.,
			pha_min=100,pha_max=None,
			hist_min=0,hist_max=2046,hist_nbin=512,
			threshold_sigma=3.0):
		sys.stdout.write('----- {} -----\n'.format(sys._getframe().f_code.co_name))

		outpdf = '%s/%s_search_burst_hist.pdf' % (self.outdir,self.basename)
		outtxt = '%s/%s_search_burst_hist.txt' % (self.outdir,self.basename)

		lchist,suffix = self.extract_curve(
			tbin=tbin,
			tmin=tmin,
			tmax=tmax,
			pha_min=pha_min,
			pha_max=pha_max)

		hist_rate_dist = Hist1D(int(hist_nbin),hist_min,hist_max)
		hist_rate_dist.fill(lchist.hist)

		fit_range_min = np.mean(lchist.hist) - 3.0 * np.std(lchist.hist)
		fit_range_max = np.mean(lchist.hist) + 3.0 * np.std(lchist.hist)	
		#print(fit_range_min,fit_range_max)
		mask_fit = np.logical_and(
			hist_rate_dist.bins>=fit_range_min,
			hist_rate_dist.bins<=fit_range_max)
		mask_data_exists = (hist_rate_dist.err > 0.0)

		chi2reg = Chi2Regression(model_gauss,
			hist_rate_dist.bins[mask_fit],hist_rate_dist.hist[mask_fit])
		fit = Minuit(chi2reg, 
			mu=np.mean(lchist.hist),
			sigma=np.std(lchist.hist),
			area=sum(hist_rate_dist.hist[mask_fit]),
			limit_mu=(0,None),
			limit_sigma=(0,None),
			limit_area=(0,None)
			)
		fit.migrad()
		fit.minos() 
		print(fit.print_param())
		print(fit.values)
		print(fit.errors)
		bestfit = fit.values

		f = open(outtxt,'w')
		f.write(str(fit.values)+'\n')
		f.write(str(fit.errors))
		f.close()

		fig = plt.figure(figsize=(7,6))
		ax1 = fig.add_axes([0.1, 0.3, 0.85, 0.68])
		ax1.errorbar(
			hist_rate_dist.bins[mask_data_exists],
			hist_rate_dist.hist[mask_data_exists],
			yerr=hist_rate_dist.err[mask_data_exists],
			marker='o',color='k',ls='',markersize=3.0)			
#			marker='o',drawstyle='steps-mid',color='k',markersize=3.0)
		ax1.plot(hist_rate_dist.bins,
			model_gauss(hist_rate_dist.bins,
				mu=bestfit['mu'],
				sigma=bestfit['sigma'], 
				area=bestfit['area']),			
			c='red',ls='--')
		threshold_rate = bestfit['mu'] + threshold_sigma * bestfit['sigma']
		ax1.axvline(x=threshold_rate,color='blue',ls='--')

		ax1.set_xlim(min(lchist.hist)-100,max(lchist.hist)+100)
		ax1.set_ylabel('Number of bins', fontsize=FONTSIZE)
		ax1.axhline(y=0.0, color='k', linestyle='--')
		#ax1.get_xaxis().set_visible(False)

		y_residual = hist_rate_dist.hist - model_gauss(hist_rate_dist.bins,
				mu=bestfit['mu'],
				sigma=bestfit['sigma'], 
				area=bestfit['area'])
		ax2 = fig.add_axes([0.1, 0.1, 0.85, 0.20])
		ax2.errorbar(
			hist_rate_dist.bins[mask_data_exists],
			y_residual[mask_data_exists],
			yerr=hist_rate_dist.err[mask_data_exists],
			marker='o',color='k',ls='',markersize=3.0)
		ax2.set_xlim(min(lchist.hist)-100,max(lchist.hist)+100)
		ax2.axhline(y=0.0, color='r', linestyle='--')
		ax2.set_xlabel('Rate (counts/%d sec)' % tbin, fontsize=FONTSIZE)
		ax2.set_ylabel('Residual', fontsize=FONTSIZE)		

		plt.tight_layout()
		plt.tick_params(axis="x",direction="in")
		plt.tick_params(axis="y",direction="in")

		axs = [ax1,ax2]
		for ax in axs:
			#ax.label_outer()	
			#ax.minorticks_on()
			ax.xaxis.grid(True)
			ax.xaxis.grid(which='major', linestyle='--', color='#000000')
			ax.xaxis.grid(which='minor', linestyle='-.')	
			ax.tick_params(axis="both", which='major', direction='in', length=5)
			ax.tick_params(axis="both", which='minor', direction='in', length=3)

		#fig.align_ylabels(axs)
		plt.tight_layout(pad=2)
		plt.rcParams["font.family"] = "serif"
		plt.rcParams["mathtext.fontset"] = "dejavuserif"		
		plt.savefig(outpdf)	

		mask_burst_candidates = lchist.hist >= threshold_rate
		print(mask_burst_candidates)
		print(lchist.bins[mask_burst_candidates])
		print(lchist.hist[mask_burst_candidates])		

		return outpdf, fit.values, fit.errors, mask_burst_candidates

	def burst_alert(self,tbin=20.0,tmin=0.0,tmax=3600.,
		pha_min=None,pha_max=None,runave_width=15,runave_threshold=3.0):
		sys.stdout.write('----- {} -----\n'.format(sys._getframe().f_code.co_name))

		if pha_min == 'None':
			pha_min = None
		if pha_max == 'None':
			pha_max = None

		lchist,suffix = self.extract_curve(tbin=tbin,tmin=tmin,tmax=tmax,
		pha_min=pha_min,pha_max=pha_max)

		# https://stackoverflow.com/questions/13728392/moving-average-or-running-mean
		runave = np.convolve(lchist.hist, np.ones(runave_width)/runave_width, 
			mode='full')[0:len(lchist.hist)]
		sigma = np.sqrt(runave * tbin)/tbin
		runave_limit = runave_threshold * sigma + runave 
		print(runave_limit)

		outpdf = '%s/%s_alert_%s.pdf' % (self.outdir,self.basename,suffix)

		fig, ax = plt.subplots(1,1, figsize=(11.69,8.27))		

		plt.errorbar(lchist.bins,lchist.hist,
			yerr=lchist.err,marker='',drawstyle='steps-mid')
		plt.plot(lchist.bins,runave,'r',linewidth=5)
		plt.plot(lchist.bins,runave_limit,'r--',linewidth=5)

		flag_glow_candidate = lchist.hist > runave_limit
		flag_edgeok = np.arange(len(lchist.hist)) > runave_width-1
		mask_burst_candidates = np.logical_and(flag_glow_candidate,flag_edgeok)
		for x in lchist.bins[mask_burst_candidates]:
			tstart = x - 0.5 * tbin 
			tstop = x + 0.5 * tbin	
			ax.axvspan(tstart, tstop, color="red", alpha=0.3)

		plt.xlabel('Time (sec)', fontsize=FONTSIZE)
		if tbin < 1.0:
			plt.ylabel('Counts/%d ms' % tbin*1000, fontsize=FONTSIZE)
		else:
			plt.ylabel('Counts/%d sec' % tbin, fontsize=FONTSIZE)
		plt.title('%s (%s ch <= pha <= %s ch, runave: wid=%d, th=%.2f)' % (self.basename,pha_min,pha_max,runave_width,runave_threshold),
			fontsize=FONTSIZE)
		#plt.xscale('log')				
		#plt.yscale('log')
		plt.xlim(tmin,tmax)
		plt.tight_layout(pad=2)
		plt.tick_params(labelsize=FONTSIZE)
		plt.rcParams["font.family"] = "serif"
		plt.rcParams["mathtext.fontset"] = "dejavuserif"		

		ax.minorticks_on()
		ax.grid(True)
		ax.grid(axis='both',which='major', linestyle='--', color='#000000')
		ax.grid(axis='both',which='minor', linestyle='--')	
		ax.tick_params(axis="both", which='major', direction='in', length=5)
		ax.tick_params(axis="both", which='minor', direction='in', length=3)
	
		plt.savefig(outpdf)	
		print(outpdf)
		return outpdf 
	
################################
# MAIN PROCESS
################################

cogamo_archive = Archive('setenv/parameter.yaml')
cogamo_archive.set_csvfiles()
cogamo_archive.convert_to_dataframe()
#cogamo_archive.process(1)
#cogamo_archive.process(307)
#cogamo_archive.process(308)
#cogamo_archive.write()
#exit()
for index in range(len(cogamo_archive.df)):
	cogamo_archive.process(index)
	cogamo_archive.write()
