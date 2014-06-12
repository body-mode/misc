import numpy as np
import pandas as pd
from collections import OrderedDict
import os
import sqlite3 as s3
import ast
import pysal as ps
import pickle

class mash_sqlite():

	def __init__(self, name):
			
		self.name = name
		self.d = {}
		self.spec_d = {}
		self.tablestr_d = {}
		
	def import_csv(self):
		print "importing csvs in current directory..."
		for fn in os.listdir('.'):
			if (fn.endswith('txt')) or (fn.endswith('csv')) and ('.' in fn):
				print fn
				self.d.update({fn.split('.')[0] : pd.read_csv(fn)})
	
	def import_dbf(self):
		print "importing dbfs in current directory..."
		for fn in os.listdir('.'):
			if fn.endswith('dbf'):
				print fn
				dbf = ps.open(fn)
				dbpass = {col: dbf.by_col(col) for col in dbf.header}
				dbdf = pd.DataFrame(dbpass)
				self.d.update({fn.split('.')[0] : dbdf})		
		
	def enforce_types(self):
		print "enforcing types..."
		for z in self.d.keys():
			print z
			for i in self.d[z].columns:
				t = [str(type(j)) for j in self.d[z][i]]
				if "<type 'str'>" in t:		
					self.d[z][i] = self.d[z][i].fillna('')
					self.d[z][i] = [str(p) for p in self.d[z][i]]
				print i, list(set(t))
		
	
	def make_specs(self):
	
		print "writing sql field types to dictionary spec_d..."
		
		
		for z in self.d.keys():
			specs = OrderedDict()
			print z
			for i in range(len(self.d[z].columns)):
				print self.d[z].columns[i]
				specs.update({self.d[z].columns[i] : str(self.d[z][self.d[z].columns[i]].dtype)})
			self.spec_d.update({z : specs})
	
	def build_tablestr(self):
		print "writing connection string to tablestr_d..."
		for z in self.d.keys():
			for j in self.spec_d[z].keys():
				if 'ID' in j:
					self.spec_d[z][j] = 'INTEGER'
				else:
					if 'int' in self.spec_d[z][j]:
						self.spec_d[z][j] = 'INTEGER'
					if 'float' in self.spec_d[z][j]:
						self.spec_d[z][j] = 'FLOAT'
					if self.spec_d[z][j] == 'object':
						self.spec_d[z][j] = 'TEXT'
			
			tablestr = [' '.join([i, k]) for i, k in self.spec_d[z].items()]
			tablestr = ', '.join(tablestr)
			self.tablestr_d.update({z : tablestr})
		
		
	
	def make_conn(self):
		print "writing to sqlite database..."
		conn = s3.connect('%s.sqlite' % (self.name))
		c = conn.cursor()
		for z in self.d.keys():
			c.execute("CREATE TABLE %s(%s);" % (z, self.tablestr_d[z]))
			
			for i in self.d[z].index:
				ro = [int(j) if type(j) == np.int64 else float(j) if type(j) == np.float64 else None if str(j) == 'nan' else j for j in self.d[z].ix[i].values]
				ro = tuple(ro)
				q = ['?' for y in range(len(self.d[z].columns))]
				q = ','.join(q)
				qstr = "INSERT INTO " + str(z) + " VALUES " + "(" + q + ")"
				c.execute(qstr, ro)
	
		conn.commit()
		
	def make_db(self):
		self.import_csv()
		self.import_dbf()
		self.enforce_types()
		self.make_specs()
		self.build_tablestr()
		self.make_conn()
	
	def save_pickle(self):
		print "saving pickle in current directory..."
		di = os.listdir('.')
		if '%s.p' % (self.name) in di:
			print "pickle already in current directory!"
		else:
			pickle.dump(self.d, open('%s.p' % (self.name), 'wb'))
		
	def save_hdf(self):
		print "saving HDF store in current directory..."
		di = os.listdir('.')
		if '%s.h5' % (self.name) in di:
			print "HDF store already in current directory!"
		else:
			h5 = pd.HDFStore('%s.h5' % (self.name))
			for i, k in self.d.items():
				h5[i] = k
			h5.close()
			
	def clear_mem(self):
		self.d = {}
		self.spec_d = {}
		self.tablestr_d = {}
