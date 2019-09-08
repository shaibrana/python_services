"""
Hooks for pre cases.
"""

import cvs_services.dal as dbm
import MySQLdb
from cvs_services.config import Connections, Headers, Response
from bottle import HTTPResponse,request
import os
import json

def initialize():
	Headers._instance=None 
	Connections._instance = None
	Response._instance = None

def initialize_child():
	Connections._instance = None
	
def get_headers(rest_headers):
# local site
#  	host = "http://localhost"




	try:
		Key = rest_headers['Key']
	except:
		Key = ""		
	
	try:
		By = "ORDER BY " + rest_headers['By'] +" "+ rest_headers['Order']
	except:
		try:
			By = "ORDER BY " + rest_headers['By']
		except:
			By = ""		
		
	try:
		if int(rest_headers['Limit']) < 100:
			Limit = "LIMIT "+rest_headers['Offset']+", "+rest_headers['Limit']
		else:
			Limit = "LIMIT "+rest_headers['Offset']+", 100"
	except:
			Limit = "LIMIT 0, 100"
			
	try:
		i  = rest_headers['Authorization'].split(' ');
		Authentication = i[1]
	except:
		Authentication = ""

	try:
		limit = rest_headers['limit']
	except:
		limit = "500"
	
	try:
		status = rest_headers['status']
	except:
		status = ""
	
	try:
		vtLimit = rest_headers['vtLimit']
	except:
		vtLimit = ""
	
	
	try:
		vtOffset = rest_headers['vtOffset']
	except:
		vtOffset = ""
	
	try:
		vtStartDate = rest_headers['vtStartDate']
	except:
		vtStartDate = ""
	
	try:
		vtEndDate = rest_headers['vtEndDate']
	except:
		vtEndDate = ""
	
	try:
		searchKeyWord = rest_headers['searchKeyWord']
	except:
		searchKeyWord = ""
	
	try:
		id = rest_headers['id']
	except:
		id = ""
	
		
	headers = {'Host':host,'Key':Key, 'By':By,'Authentication':Authentication, 'Limit':Limit,'limit': limit,'status':status,'searchKeyWord':searchKeyWord,'vtEndDate':vtEndDate,'vtStartDate':vtStartDate, 'vtOffset':vtOffset,'vtLimit':vtLimit,'id':id}
	
	mckey = memcache_key(headers)
	headers['mckey']=mckey
	Headers(headers)
	
def get_body(rest_body):
	print rest_body

def authenticate():
	key = Headers()['Key']
	
	host_check = request.environ['REMOTE_ADDR']
	
	print host_check
	print key
		
	if not key:
		response = {}
		response['status'] ="Failure"
		response['message']="Missing API Key, please provide key to access our system."
		raise HTTPResponse(json.dumps(response), content_type="application/json")
	
 	if key != 'VcCz8vqHuJ4UkR4Y4tqC-k734CEsv58cN215R9Dw1':
 		response = {}
 		response['status'] = 'Failure'
 		response['message'] = 'Invalid API Key.'
 		raise HTTPResponse(json.dumps(response), content_type="application/json")
	
	
def establish_connection():    
	
	try:
		
# 		localhost
#  		mysqldbconnection = MySQLdb.connect('localhost', 'test', 'test', 'test', use_unicode=True, charset="utf8", init_command='SET NAMES UTF8')

			
		
		Connections(mysqldbconnection)
	
	except MySQLdb.Error, e: 
		print "Error %d: %s" % (e.args[0],e.args[1])
	
def memcache_key(values):
	mkey = ""
	for val in values:
		if val != "":
			mkey+= values[val].replace(" ", "_") + "_"
	return mkey

def close_conn():
	try:
		mysqldb = Connections()['mysqldbconnection']
		mysqldb.close()
	except:
		pass
