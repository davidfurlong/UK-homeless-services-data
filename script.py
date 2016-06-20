#! python 3

import sys, requests, psycopg2, bs4, time
from pymongo import MongoClient

# sys.argv

# todo is next_sibling or next_element correct?

# conn = psycopg2.connect(database="homeless", user="postgres",  host="127.0.0.1", port="5432")

client = MongoClient()
db = client.homeless

baseUrl = 'http://www.homelessuk.org/'
indexesFile = open('indexes.txt', 'r')
# indexesFile = ["details.asp?id=HO1007401","Advice service"] # for testing only!
# indexesFile = ['details.asp?id=UK28329', 'Accommodation']

prevLine = "";
flag = False
count = 0
for line in indexesFile:
	if line[:11] != "details.asp" and not(flag):
		continue
	if not(flag): # iff currently reading URL
		prevLine = line
		flag = True
		continue
	flag = False
	count += 1
	print count
	url = baseUrl + prevLine.strip()
	res = requests.get(url)
	if res.status_code == requests.codes.ok:
		# todo catch error
		p = bs4.BeautifulSoup(res.text)
		# get name of project
		project_name = p.select('#title')[0].string
		# Who the project is for, Service Offered, How to Contact, Access Information, Further information
		
		# Referral address, Address, Phone, Email, Website, Fax, Minicom
		data = {}
		data[u'identifier'] = prevLine[15:] 
		data[u'Category'] = unicode(line, "utf-8")
		data[u'Name'] = project_name
		# captures all h3 elements and their contents
		for heading in p.find_all("h3"):
			key = heading.contents[0].strip()
			attrParent = heading.next_sibling
			attr = ""
			for string in attrParent.stripped_strings:
			    attr += string
			data[key] = attr

		# captures all unlabeled descriptions of h2 elements 
		for heading in p.find_all("h2"):
			if len(heading.contents) > 0 and len(heading.next_sibling.contents) > 0:
				key = heading.contents[0].strip()
				attrParent = heading.next_sibling.contents[0]
				if attrParent.name == "p":
					attr = ""
					for string in attrParent.stripped_strings:
						attr += string
					data[key] = attr
		
		# captures all captions
		for heading in p.find_all("caption"):
			if len(heading.contents) > 0 and len(heading.next_sibling.contents) > 0:
				key = heading.contents[0].strip()
				attrParent = heading.next_sibling.contents[0]
				if attrParent.parent.name == "tbody":
					attr = []
					for row in attrParent.parent.children:
						rowVal = []
						for col in row.children:
							rowVal.append(col.string)
						attr.append(rowVal)
					data[key] = attr

		db.homelessUK.insert(data);
		# todo save data to postgres
	else:
		print "request for " + line + " failed"
		# log failed requests

