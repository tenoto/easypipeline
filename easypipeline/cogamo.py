# -*- coding: utf-8 -*-
# Last modified 2023-07-06

import os
import re
import sys
import numpy as np
import pandas as pd 

from astropy.time import Time
from datetime import datetime, timedelta, timezone
tz_tokyo = timezone(timedelta(hours=+9), 'Asia/Tokyo')
tz_utc = timezone(timedelta(hours=0), 'UTC')

import matplotlib.pylab as plt 
import matplotlib.dates as dates

class HKData():
	"""
	1. yyyy-mm-dd (JST)
	2. HH:MM:SS (JST)
	3. data recording interval (min)
	4. rate1 (cps) below "AREABD1" of " config.csv"
	5. rate2 (cps) between "AREABD1" and  "AREABD2" of " config.csv"
	6. rate3 (cps) between "AREABD2" and  "AREABD3" of " config.csv"
	7. rate4 (cps) between "AREABD3" and  "AREABD4" of " config.csv"
	8. rate5 (cps) between "AREABD4" and  "AREABD5" of " config.csv"
	9. rate6 (cps) above "AREABD5" of " config.csv"
	10. temperature (degC)
	11. pressure (hPa)
	12. humidity (%)
	13. the maximum value among the difference of 10-sec moving average of count rates to the latest count rates (10秒移動平均とCPS値との差の最大値:定義を確認する必要がある) 
	14. optical illumination (lux)
	15. n/a
	16. gps status (0:invalid, 1 or 2: valid)
	17. longitude (deg)
	18. latitude (deg)
	"""
	def __init__(self, filepath):	
		self.filetype = None		
		self.filepath = filepath
		self.filename = os.path.basename(self.filepath)
		self.basename = os.path.splitext(self.filename)[0]

		self.param = {}
		self.pdflist = []

		self.set_filetype()
		self.open_file()
		self.set_time_series()

	def set_filetype(self):
		if re.fullmatch(r'\d{3}_\d{8}.csv', self.filename):
			self.filetype = 'rawcsv'
			self.detid_str, self.yyyymmdd_jst = self.basename.split("_")		
			self.year = self.yyyymmdd_jst[0:4]
			self.month = self.yyyymmdd_jst[4:6]
			self.day = self.yyyymmdd_jst[6:8]			
		else:
			sys.stdout.write("[error] filetype error...")
			return -1

	def open_file(self):
		if not os.path.exists(self.filepath):
			raise FileNotFoundError("{} not found".format(self.filepath))
		try:
			#cmd = ' nkf -w --overwrite %s' % self.filepath
			#print(cmd);os.system(cmd)

			if self.filetype == 'rawcsv':
#				self.df = pd.read_csv(self.filepath, index_col=False, on_bad_lines='skip', encoding='utf-8',
				self.df = pd.read_csv(self.filepath, index_col=False, encoding='utf-8',
					names=['yyyymmdd','hhmmss','interval','rate1','rate2','rate3','rate4','rate5','rate6','temperature','pressure','humidity','differential','lux','n/a','gps_status','longitude','latitude'],
					dtype={})
				self.nevents = len(self.df)

				# sometimes two lines are collapsed. This process excludes these lines. 
				#flag = pd.to_numeric(self.df['latitude'],errors='coerce').isnull()
				#self.df = self.df[~flag]

			else:
				sys.stdout.write("[error] filetype error...")
				return -1
		except OSError as e:
			sys.stderr.write("[OSError]")
			raise

		sys.stdout.write('[HKData] open {}\n'.format(self.filepath))	

	def set_time_series(self):		
		sys.stdout.write('----- {} -----\n'.format(sys._getframe().f_code.co_name))

		tmp_time_series_str = np.char.array(self.df['yyyymmdd'] + 'T' + self.df['hhmmss'])
		tmp_time_series_jst = Time(tmp_time_series_str, format='isot', scale='utc', precision=5) 	
		tmp_time_series_utc = tmp_time_series_jst - timedelta(hours=+9)		
		self.df['unixtime'] = tmp_time_series_utc.to_value('unix',subfmt='decimal')
		self.df['unixtime'] = self.df['unixtime'].astype(np.float64)
		self.df['jst'] = tmp_time_series_jst

	def set_outdir(self,outdir_root,flag_overwrite=True):
		self.outdir_root = outdir_root
		self.outdir = '%s/data/%s' % (self.outdir_root, self.basename)

		if flag_overwrite:
			cmd = 'rm -rf %s' % self.outdir
			print(cmd);os.system(cmd)

		if not os.path.exists(self.outdir):
			cmd = 'mkdir -p %s' % self.outdir
			print(cmd);os.system(cmd)

	def plot(self,outpdf,tstart=None,tstop=None,ylog=0):
		sys.stdout.write('----- {} -----\n'.format(sys._getframe().f_code.co_name))		
		time_series_utc = Time(self.df['unixtime'],format='unix',scale='utc')
		time_series_jst = time_series_utc.to_datetime(timezone=tz_tokyo)
		plt.rcParams['timezone'] = 'Asia/Tokyo'

		title  = 'DET_ID=%s ' % self.detid_str
		title += '(Longitude=%.3f deg, ' % (np.mean(pd.to_numeric(self.df['latitude'],errors='coerce')))
		title += 'Latitude=%.3f deg)' % (np.mean(pd.to_numeric(self.df['longitude'],errors='coerce')))		
		title += '\n'
		title += '%s ' % str(time_series_jst[0])[0:10]
		title += 'Interval=%d sec ' % (self.df['interval'][0])
		title += '(%s)' % self.filename
		title += '\n'		
		#if self.hdu['HK'].header['AREABD2'] > 0.0:
		#	title += 'Rate L (1+2):<%.1f MeV, ' % (self.hdu['HK'].header['AREABD2']/1000.0)
		#	title += 'Rate M (3+4):%.1f-%.1f MeV, ' % (self.hdu['HK'].header['AREABD2']/1000.0,self.hdu['HK'].header['AREABD4']/1000.0)		
		#	title += 'Rate H (5+6):>%.1f MeV, ' % (self.hdu['HK'].header['AREABD4']/1000.0)
		title += 'Rate L (1+2):<1 MeV, ' 
		title += 'Rate M (3+4):1-3 MeV, '
		title += 'Rate H (5+6):>3 MeV '

		if tstart is not None and tstop is not None:
			tmp_tstart_jst = Time(tstart, format='isot', scale='utc', precision=5) 	
			tmp_tstart_utc = tmp_tstart_jst - timedelta(hours=+9)		
			tstart_jst = tmp_tstart_utc.to_datetime(timezone=tz_tokyo)

			tmp_tstop_jst = Time(tstop, format='isot', scale='utc', precision=5) 	
			tmp_tstop_utc = tmp_tstop_jst - timedelta(hours=+9)		
			tstop_jst = tmp_tstop_utc.to_datetime(timezone=tz_tokyo)		

			flag = np.logical_and(time_series_jst >= tstart_jst,time_series_jst <= tstop_jst)
			time_series_jst = time_series_jst[flag]				
			self.df = self.df[flag]

		# color https://matplotlib.org/stable/tutorials/colors/colors.html
		fig, axs = plt.subplots(8,1, figsize=(8.27,11.69), 
			sharex=True, gridspec_kw={'hspace': 0})
		axs[0].step(
			time_series_jst,
			self.df['rate1']+self.df['rate2'],
			'-', c='salmon',mec='k', markersize=2,where='mid')
		axs[0].set_ylabel(r"Rate L (cps)")
		axs[0].set_title(title)	
		if ylog == 1: axs[0].set_yscale('log')
		axs[1].step(
			time_series_jst,
			self.df['rate3']+self.df['rate4'],
			'-', c='tomato',mec='k', markersize=2,where='mid')
		axs[1].set_ylabel(r"Rate M (cps)")	
		if ylog == 1: axs[1].set_yscale('log')		
		axs[2].step(
			time_series_jst,
			self.df['rate5']+self.df['rate6'],
			'-',c='red',mec='k', markersize=2,where='mid')
		axs[2].set_ylabel(r"Rate H (cps)")				
		if ylog == 1: axs[2].set_yscale('log')				
		axs[3].step(time_series_jst,self.df['temperature'],
			'-',c='k',where='mid')
		axs[3].set_ylabel(r"Temp. (degC)")
		axs[4].step(time_series_jst,self.df['pressure'],
			'-',c='blue',where='mid')
		axs[4].set_ylabel(r"Press. (hPa)")		
		axs[5].step(time_series_jst,self.df['humidity'],
			'-',c='yellowgreen',where='mid')
		axs[5].set_ylabel(r"Humid. (%)")
#		axs[6].step(time_series_jst,self.df['differential'],where='mid')		
#		axs[6].set_ylabel(r"Diff (cps)")	
#		axs[6].set_yscale('log')		
		axs[6].step(time_series_jst,self.df['lux'],
			'-',c='purple',where='mid')		
		axs[6].set_yscale('log')
		axs[6].set_ylabel(r"Illum.")
		axs[7].step(time_series_jst,self.df['gps_status'],
			'-',c='sienna',where='mid')		
		axs[7].set_ylabel(r"GPS status")		
		axs[7].set_xlabel(r"Time (JST)")
		axs[7].set_ylim(-0.5,2.5)
		axs[7].xaxis.set_major_formatter(dates.DateFormatter('%m-%d\n%H:%M'))

		if tstart is not None and tstop is not None:
			tmp_tstart_jst = Time(tstart, format='isot', scale='utc', precision=5) 	
			tmp_tstart_utc = tmp_tstart_jst - timedelta(hours=+9)		
			tstart_jst = tmp_tstart_utc.to_datetime(timezone=tz_tokyo)
			tmp_tstop_jst = Time(tstop, format='isot', scale='utc', precision=5) 	
			tmp_tstop_utc = tmp_tstop_jst - timedelta(hours=+9)		
			tstop_jst = tmp_tstop_utc.to_datetime(timezone=tz_tokyo)
			axs[7].set_xlim(tstart_jst,tstop_jst)
		else:
			axs[7].set_xlim(time_series_jst[0],time_series_jst[-1])

		for ax in axs:
			ax.label_outer()	
			ax.minorticks_on()
			ax.xaxis.grid(True)
			ax.xaxis.grid(which='major', linestyle='--', color='#000000')
			ax.xaxis.grid(which='minor', linestyle='-.')	
			ax.xaxis.set_minor_locator(dates.HourLocator())
			ax.tick_params(axis="both", which='major', direction='in', length=5)
			ax.tick_params(axis="both", which='minor', direction='in', length=3)			

		fig.align_ylabels(axs)
		plt.tight_layout(pad=2)
		plt.rcParams["font.family"] = "serif"
		plt.rcParams["mathtext.fontset"] = "dejavuserif"		
		plt.savefig(outpdf)		

	def run(self,piptable,index):
		self.set_outdir(piptable.outdir)

		### add basic information to the table 
		piptable.df.iloc[index]['DetID'] = self.detid_str
		piptable.df.iloc[index]['Interval'] = self.df['interval'][0]
		piptable.df.iloc[index]['Date'] = str(self.df['jst'][0])[0:10]

		### add quick look (QL) curve plot
		qlplot_fname = '%s.pdf' % self.basename
		qlplot_path = '%s/%s.pdf' % (self.outdir,self.basename)		
		self.plot(outpdf=qlplot_path)
		piptable.df.iloc[index]['qlplot'] = '<a href=\"../%s\">%s</a>' % (qlplot_path,qlplot_fname)



