#!/usr/bin/python
# -*- coding: utf-8 -*-
__NOTICE__ = '''
upload_mps.py
Pull images from beta.parliament.uk

param 1 = skip to letter (A=1)

Date:
	2017 May create
	2018 Mar update to cover House of Lords photos, by request

Author: Fae, http://j.mp/faewm
Permissions: CC-BY-SA-4.0
'''

import pywikibot, upload, sys, urllib2, urllib, re, string, time, os
import webbrowser, cookielib, json, datetime
from pywikibot import pagegenerators
from BeautifulSoup import BeautifulSoup
from sys import argv
from sys import stdout
from time import sleep
from os import remove
from colorama import Fore, Back, Style
from colorama import init
init()

# SSL/TLS reach-around
import shutil, urllib3, certifi
http = urllib3.PoolManager(cert_reqs='CERT_REQUIRED', ca_certs=certifi.where())


site = pywikibot.getSite('commons', 'commons')

# URL not whitelisted
def up(filename, pagetitle, desc, comment):
	if filename[:4] == 'http':
		source_url=filename; source_filename=None
	else:
		source_url=None; source_filename=filename
		site.upload(pywikibot.ImagePage(site, 'File:' + pagetitle),
		source_filename=source_filename, 
		source_url=source_url,
		comment=comment, 
		text=desc, 
		watch=False, 
		ignore_warnings=True,
		chunk_size=1048576)
		return
	url = source_url
	keepFilename=True        #set to True to skip double-checking/editing destination filename
	verifyDescription=False    #set to False to skip double-checking/editing description => change to bot-mode
	targetSite = pywikibot.getSite('commons', 'commons')
	bot = upload.UploadRobot(
		[url], # string gives depreciation msg
		description=desc, # only one description if multiple images
		useFilename=pagetitle,
		keepFilename=keepFilename, 
		verifyDescription=verifyDescription, 
		targetSite = targetSite,
		ignoreWarning = True,
		chunk_size=2000000 # 2MB
		)
	bot.upload_file(file_url=url, debug=True)

def uptry(source,filename,desc, comment):
		countErr=0
		r=True
		while r:
				try:
						up(source,filename,desc, comment)
						return
				except Exception as e:
						countErr+=1
						if countErr>2: return
						print Fore.RED, str(e), Fore.WHITE
						if re.search("duplicate|nochange", str(e).lower()):
							return
						print Fore.CYAN,'** ERROR Upload failed',Fore.WHITE
						time.sleep(2)
		return

def urltry(u, headers = { 'User-Agent' : 'Netscape/5.0' } ):
	countErr=0
	x=''
	while x=='':
		try:
			req = urllib2.Request(u, None, headers)
			x = urllib2.urlopen(req)
			time.sleep(1)
		except:
			x=''
			countErr+=1
			if countErr>300: countErr=300	#	5 minutes between read attempts, eventually
			print (Fore.CYAN + '** ERROR {}\n ** Failed to read from '+ Fore.YELLOW +'{}'+ Fore.CYAN +'\n ** Pause for {} seconds and try again [{}]' + Fore.WHITE).format(countErr, u, countErr*1, time.strftime("%H:%M:%S"))
			time.sleep(1*countErr)
			
	return x

def htmltry(x,u):
		countErr=0
		r=True
		while r:
				try:
						return x.read()
				except:
						x=urltry(u)
						countErr+=1
						if countErr>200:
								p=300
						else:
								p=countErr*2
						print Cyan,'** ERROR',countErr,'\n ** Failed to read xml'
						if countErr==1:
								print Fore.BLUE +'xml ='+str(x)
								print 'url ='+u+ Fore.CYAN
						print ' ** Pause for '+str(p)+' seconds and try again'+ Fore.WHITE
						time.sleep(p)
				else:
						r=False
		return

def uptry(source, filename, desc, comment):
		countErr=0
		r=True
		while r:
				try:
						up(source, filename, desc, comment)
						return
				except Exception as e:
						countErr+=1
						p=countErr*5
						print Fore.CYAN,'** ERROR Upload failed'
						if countErr > 4: return
						print Fore.RED, str(e), Fore.CYAN
						print ' ** Pause for '+str(p)+' seconds and try again'+ Fore.WHITE
						time.sleep(p)
		return
	
print Fore.GREEN + '*' *80,
print __NOTICE__
print '*' * 80, Fore.WHITE

LOCALDIR = '/Volumes/RAM Disk/'
if not os.path.exists(LOCALDIR):
	print Fore.MAGENTA + "RAM Disk or alternative must be set up"
	sys.exit()

skipl = 0
skipi = 0
if len(argv)>1:
	skipl = int(float(argv[1]))
if len(argv)>2:
	skipi = int(float(argv[2]))
	
print skipl, skipi
	
count=0
uploadcount = 0

domain = "https://beta.parliament.uk"
base = "https://beta.parliament.uk/houses/WkUWUBMx/members/current/a-z/{}"

for asc in range(1, 27):
	if asc<skipl: continue
	letter = chr(64 + asc)
	print Fore.MAGENTA + "Browse from {} ({})".format(letter, asc), Fore.WHITE
	url = base.format(letter.lower())
	uri = urltry(url)
	lsoup = BeautifulSoup(htmltry(uri, url))
	gpages = lsoup.findAll('a', href=re.compile("/people/*"))
	print len(gpages), 'people found under', letter
	gcount = 0
	for gpage in gpages:
		gcount += 1
		url = domain + gpage['href']
		print Fore.GREEN + "{} {}/{}".format(letter, gcount, len(gpages)), Fore.CYAN + url, Fore.YELLOW + time.strftime("%H:%M:%S") + Fore.WHITE
		uri = urltry(url)
		lsoup = BeautifulSoup(htmltry(uri, url))
		mediaurl = lsoup.find('a', href=re.compile("/media/*"))
		if mediaurl is None:
			continue
		print Fore.CYAN, domain + mediaurl['href'], Fore.WHITE
		uri = urltry(domain + mediaurl['href'])
		msoup = BeautifulSoup(htmltry(uri, mediaurl))
		sources = msoup.findAll('a', href=re.compile(".*/photo/.*download=true"))
		scount = 0
		head = msoup.find('h1').contents[0]
		for s in sources:
			source = s['href']
			if len(sources)>1:
				sscount = 0
				gallery = "<gallery>"
				for ss in sources:
					if ss != s:
						gallery += "\n" + head
						if sscount!=0:
							gallery += " crop {}".format(sscount)
						gallery += ".jpg"
					sscount += 1
				gallery += "\n</gallery>"
			desc = s.text
			if scount>0:
				title = head + " crop {}.jpg".format(scount)
			else:
				title = head + ".jpg"
			scount += 1
			page = pywikibot.Page(site, "File:" + title)
			if page.exists():
				continue
			print Fore.MAGENTA + title, Fore.WHITE
			source=source.split('?')[0]
			print Fore.GREEN, source, desc, Fore.WHITE
			dd = "=={{int:filedesc}}==\n{{Information"
			dd+= "\n|description={{en|1=" + head + "}}"
			dd+= "\n|author = {{Creator:Chris McAndrew}}"
			dd+= "\n|date=2018-03"
			dd+= "\n|source = "+ source + "\n:Gallery: " + domain + mediaurl['href']
			dd+= "\n|permission = For confirmation of licence, see https://pds.blog.parliament.uk/2017/07/21/mp-official-portraits-open-source-images/"
			dd+= "\n|other versions = " + gallery
			dd+= "\n}}\n\n=={{int:license-header}}==\n{{cc-by-3.0}}\n"
			dd+= "\n[[Category:Official United Kingdom Parliamentary photographs 2017]]"
			dd+= "\n[[Category:Images uploaded by {{subst:User:Fae/Fae}}]]"
			comment = head
			loop = True
			lcount = 0
			local = LOCALDIR + 'mp.jpg'
			rloop = True
			while rloop:
				try:
					#urllib.urlretrieve not working due to new site security
					with http.request('GET', source, preload_content=False) as resp, open(local, 'wb') as out_file:
						shutil.copyfileobj(resp, out_file)
					resp.release_conn()
					rloop = False
				except Exception as e:
					print Fore.RED + str(e), Fore.WHITE
					sleep(30)
			while loop:
				try:
					uptry(local, title, dd, comment)
					#print dd
					loop=False
				except Exception as e:
					lcount+=1
					if lcount>3:
						print "Giving up trying to upload after",lcount,"tries"
						loop=False
						continue
					print Fore.RED+"PROBLEM UPLOADING", str(e)
					print "[re-attempt",lcount,"of 3]",time.strftime("%H:%M:%S")+Fore.WHITE
					sleep(5)
				remove(local)
