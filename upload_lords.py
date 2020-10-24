#!/usr/bin/python
# -*- coding: utf-8 -*-
__NOTICE__ = '''
upload_lords.py
also refer to upload_house_of_commons.py
Pull images from parliament.uk for House of Lords

Date:
	2017 May create.
	2018 Mar fork to cover House of Lords photos, by request.
	2020 Add EXIF detection of date/photographer.
		 There are unused modules and dead code here!
	2020 Oct force year in filenames, match commons script.

Author: Fae, http://j.mp/faewm
Permissions: CC-BY-SA-4.0

Command line
python pwb.py upload_lords.py <optional filter regex>
'''

import pywikibot, upload, sys, urllib2, urllib, re, string, time, os
import json, datetime, exiftool
from pywikibot import pagegenerators
from BeautifulSoup import BeautifulSoup
from sys import argv
from sys import stdout
from time import sleep
from os import remove
from colorama import Fore, Back, Style
from colorama import init
init()
from titlecase import titlecase

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
		ignore_warnings=True, # True if ignoring duplicates
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

print Fore.GREEN + '*' *80,
print __NOTICE__
print '*' * 80, Fore.WHITE

LOCALDIR = '/home/ashley/Downloads/TEMP/'
if not os.path.exists(LOCALDIR):
	print Fore.MAGENTA + "RAM Disk or alternative must be set up"
	sys.exit()

regex = ''
skipl = 0
skipi = 0
if len(argv)>1:
	skipl = int(float(argv[1]))
if len(argv)>2:
	skipi = int(float(argv[2]))

count=0
uploadcount = 0

domain = "https://members.parliament.uk"

base = "https://members.parliament.uk/members/Lords"

url = base + "?page=1"
uri = urltry(url)
soup = BeautifulSoup(htmltry(uri, url))
maxp = int(float(soup.find('div', {"class":"result-text"}).text.split('of')[-1].split(')')[0]))
print Fore.GREEN, "Total pages in gallery", maxp, "each with 20 members", Fore.WHITE
ucount = 0
for p in range(1, maxp+1):
	url = base + "?page=" + str(p)
	print url
	if p < skipl:
		continue
	uri = urltry(url)
	lsoup = BeautifulSoup(htmltry(uri, url))
	gpages = lsoup.findAll('a', href=re.compile("/member/.*/contact")) #https://members.parliament.uk/member/172/portrait
	print len(gpages), 'people found on page', p
	gcount = 0
	for gpage in gpages:
		gcount += 1
		giveup = False
		url = domain + re.findall(r"\/member\/\d*", gpage['href'])[0] + "/portrait"
		print Fore.GREEN + "{}/{} {}/{}".format(p, maxp, gcount, len(gpages)), Fore.CYAN + url, Fore.YELLOW + time.strftime("%H:%M:%S") + Fore.WHITE
		uri = urltry(url)
		lsoup = BeautifulSoup(htmltry(uri, url))
		#https://members-api.parliament.uk/api/Members/172/Portrait?cropType=FullSize&webVersion=false
		sources = lsoup.findAll('img', src=re.compile(".*Portrait\?cropType.*"))
		if len(sources)<4:
			continue
		scount = 0
		head = "Official portrait of " + lsoup.find('h1').contents[0]
		if regex != '':
			if not re.search(regex, head):
				continue
		loop = True
		lcount = 0
		local = LOCALDIR + 'lord.jpg'
		try:
			remove(local)
		except:
			pass
		rloop = True
		source = sources[0]['src'] + "&webVersion=false"
		print source
		while rloop:
			try:
				urllib.urlretrieve(source, local)# not working due to new site security
				'''with http.request('GET', source, preload_content=False) as resp, open(local, 'wb') as out_file:
					shutil.copyfileobj(resp, out_file)
				resp.release_conn()'''
				rloop = False
			except Exception as e:
				print Fore.RED + str(e), Fore.WHITE
				sleep(30)
		with exiftool.ExifTool() as et:
			metadata = et.get_metadata(local)
		#print metadata
		artist,date = '',''
		for k in ['XMP:Creator', 'EXIF:Artist']:
			if k in metadata.keys():
				print Fore.CYAN, k, Fore.YELLOW, metadata[k], Fore.WHITE
				artist = metadata[k]
				break
		for k in ['XMP:DateCreated', 'XMP:MetadataDate']:
			if k in metadata.keys():
				print Fore.CYAN, k, Fore.YELLOW, metadata[k], Fore.WHITE
				date = metadata[k]
				break
		if date == '':
			continue
		year = date[:4]
		if int(float(year)) < 2020:
			print Fore.MAGENTA, "year", year, Fore.WHITE
			continue
		date = re.sub(":", "-", date.split(' ')[0])
		for s in sources:
			if giveup: continue
			atitle = re.sub(":", u"×", s['alt'])
			source = s['src']
			if len(sources)>1:
				sscount = 0
				gallery = "<gallery>"
				for ss in sources:
					if ss != s:
						gallery += "\n" + head + " " + year
						if sscount!=0:
							gallery += " crop {}".format(sscount)
						gallery += ".jpg"
					sscount += 1
				gallery += "\n</gallery>"
			desc = s.text
			if scount>0:
				title = head + " " + year + " crop {}.jpg".format(scount)
				btitle = head + " " + year + " crop {}.jpg".format(scount)
			else:
				title = head + " " + year + ".jpg"
				btitle = head + " " + year + ".jpg"
			scount += 1
			page = pywikibot.Page(site, u"File:" + title)
			pageb = pywikibot.Page(site, u"File:" + btitle)
			pagec = pywikibot.Page(site, u"File:" + head + ".jpg")
			if pageb.exists():
				print Fore.RED, "Page exists", pageb.title(), Fore.WHITE
				giveup = True
				continue
			if pagec.exists():
				html = pagec.get()
				try:
					cyear = html.split("|date= ")[1].split('-')[0]
					if cyear == year:
						print Fore.RED, "Old page exists", pagec.title()
						print " and year is", cyear
						giveup = True
						continue
				except:
					pass
			print Fore.MAGENTA + title, Fore.WHITE
			print Fore.GREEN, source, desc, Fore.WHITE
			dd = "=={{int:filedesc}}==\n{{Information"
			dd+= "\n|description={{en|1=" + head + "\n*" + atitle + "}}"
			dd+= "\n|author = " + titlecase(artist)
			dd+= "\n|date= " + date
			dd+= "\n|source = "+ source + "\n:Gallery: " + url
			dd+= "\n|permission = "
			dd+= "\n|other versions = " + gallery
			dd+= "\n}}\n\n=={{int:license-header}}==\n{{cc-by-3.0}}\n"
			dd+= "\n[[Category:Official United Kingdom Parliamentary photographs " + year + "]]"
			dd+= "\n[[Category:Images uploaded by {{subst:User:Fae/Fae}}]]"
			comment = u"[[User:Fæ/Project list/United Kingdom Parliamentary photographs|Parliamentary photographs batch upload]]: {} {}".format(head, year)
			loop = True
			lcount = 0
			rloop = True
			while rloop:
				try:
					if scount>1:
						urllib.urlretrieve(source + "&webVersion=false", local)
					rloop = False
				except Exception as e:
					print Fore.RED + str(e), Fore.WHITE
					sleep(30)
			while loop:
				try:
					ures = uptry(local, title, dd, comment)
					if ures in ['duplicate']:
						giveup = True
					if ures in ['retrieval incomplete']:
						lcount += 1
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
