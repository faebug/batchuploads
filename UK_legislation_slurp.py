#!/usr/bin/python
# -*- coding: utf-8 -*-
__NOTICE__ = '''
UK_legislation_slurp.py
[[Commons:UK legislation project]]
Whitelist request https://phabricator.wikimedia.org/T265690

Slurp latest legislation only, stop when next page returns nothing new.

Meant to run from chrontab as a daily or weekly task:
nice -n 20 python pwb.py uklegislation_slurp

Warning, bit hacky, some redundant code here!
'''

import requests, os, lxml
import pywikibot, upload, sys, urllib2, urllib, re, string, time
from bs4 import BeautifulSoup
from pywikibot import pagegenerators
from sys import argv
from sys import stdout
from time import sleep
from colorama import Fore, Back, Style
from colorama import init
init()

import pprint
pp = pprint.PrettyPrinter(indent=4)

#	Colours only on mac
Red="\033[0;31m"     #Red
Green="\033[0;32m"   #Green
GreenB="\033[1;32m"	#Green bold
GreenU="\033[4;32m"	#Green underlined
Yellow="\033[0;33m"  #Yellow
Blue="\033[0;34m"    #Blue
Purple="\033[0;35m"  #Purpley
Cyan="\033[0;36m"    #Cyan
White="\033[0;37m"   #White

site = pywikibot.getSite('commons', 'commons')
YEAR = int(float(time.strftime("%Y")))
DIR = os.path.join(os.path.expanduser('~'), 'Downloads', 'TEMP')

def up(source, pagetitle, desc, comment, iw):
	if source[:4] == 'http':
		source_url=source; source_filename=None
		# Resolve url redirects to find end target (the API will not do this)
		headers = { 'User-Agent' : 'Mozilla/5.0' }
		req = urllib2.Request(source_url, None, headers)
		res = urllib2.urlopen(req)
		source_url = res.geturl()
	else:
		source_url=None; source_filename=source

	if iw:
		site.upload(pywikibot.FilePage(site, 'File:' + pagetitle),
			source_filename=source_filename,
			source_url=source_url,
			comment=comment,
			text=desc,
			ignore_warnings = True,
			chunk_size= 400000,#1048576,
			#async = True,
			)
	else:
		site.upload(pywikibot.FilePage(site, 'File:' + pagetitle),
			source_filename=source_filename,
			source_url=source_url,
			comment=comment,
			text=desc,
			ignore_warnings = False,
			chunk_size = 400000,#1048576,
			#async = True,
			)

def uptry(source, filename, desc, comment, iw):
		countErr=0
		r=True
		while r:
				try:
						up(source, filename, desc, comment, iw)
						return ''
				except Exception as e:						
						countErr+=1
						try:
							ecode = e.code
						except Exception as ee:
							ecode = str(e)
						if re.search("ratelimited", str(e)):
							print Fore.MAGENTA, ecode, Fore.WHITE
							wait = min(60*countErr, 300)
							print Fore.GREEN, "Sleeping for {}s".format(wait), Fore.WHITE
							sleep(wait)
							if countErr>3:
								countErr = 3
								print Fore.MAGENTA, "Consider increasing ratelimit lag of", ratelimit, Fore.WHITE
						if re.search("multiple", str(e)):
							print Fore.MAGENTA, ecode, Fore.WHITE
						if re.search("429", str(ecode)):
							# Too many requests
							wait = min(30*countErr, 300)
							print Fore.MAGENTA, "Too many requests" + Fore.GREEN,
							if wait>90:
								print Fore.RED,
							print "Wait {}s".format(wait),
							if wait>30:
								cumwait = countErr * (countErr + 1.) * 15.
								print "(total {:.3g}m)".format(cumwait/60.),
							print Fore.WHITE
							sleep(wait)
							continue
						if re.search('File exists with different extension', str(ecode)):
							print Fore.MAGENTA, ecode, Fore.WHITE
							return ''
						if re.search('The uploaded file contains errors', str(ecode)):
							print Fore.MAGENTA, ecode, Fore.WHITE
							return ''
						if re.search('exists-normalized', str(ecode)):
							#print Fore.MAGENTA, ecode, Fore.WHITE
							iw = True
							continue
						if re.search("was-deleted", str(e)):
							print Fore.MAGENTA, ecode, Fore.WHITE
							print Fore.RED, "Already deleted, skipping", Fore.WHITE
							return ''
						if re.search('fileexists-shared-forbidden', str(ecode)):
							print Fore.MAGENTA, ecode, Fore.WHITE
							return ''
						if re.search('fileexists-no-change', str(ecode)):
							print Fore.MAGENTA, ecode, Fore.WHITE
							return ''
						if re.search('exists', str(ecode)):
							if countErr>10:
								print Fore.RED, countErr, "tries made, skipping", Fore.WHITE
								return ''
							if countErr>1:
								print Fore.MAGENTA, countErr, ecode, Fore.WHITE
							iw = True
							continue
						if re.search("image/png", str(e)):
							return "png"
						if re.search("image/tiff", str(e)):
							return "tiff"
						if re.search("verification-error", str(e)):
							print Fore.RED, "Verification error, bad format", Fore.WHITE
							if countErr>1:
								return 'verification-error'
							continue
						if re.search("chunk-too-small", str(e)):
							print Fore.RED, "chunk-too-small", Fore.WHITE
							if countErr>1:
								return 'chunk-too-small'
							continue
						if re.search("script code", str(e)):
							print Fore.RED, "Looks like a bad file format", Fore.WHITE
							return ''
						if re.search("copyuploadbaddomain", str(e)):
							print Fore.RED, "Bad domain for url upload", Fore.WHITE
							sleep(60)
							return ''
						if countErr>4: return
						print Fore.RED, str(e), Fore.WHITE
						if re.search("duplicate|nochange", str(e).lower()):
							return ''
						print Fore.MAGENTA, ecode, Fore.WHITE
						#print Fore.CYAN,'** ERROR Upload failed', Fore.WHITE
						time.sleep(1)
		return ''

def urltry(u):
	headers = { 'User-Agent' : 'Mozilla/5.0' } # Spoof header
	countErr=0
	x=''
	while x=='':
			try:
					req = urllib2.Request(u,None,headers)
					x = urllib2.urlopen(req)
					time.sleep(1)
			except:
					x=''
					countErr+=1
					if countErr>3: return ' '
					if countErr>300: countErr=300	#	5 minutes between read attempts, eventually
					print Cyan,'** ERROR',countErr,'\n ** Failed to read from '+Yellow+u+Cyan+'\n ** Pause for '+str(countErr*1)+' seconds and try again ['+time.strftime("%H:%M:%S")+']',White
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
								print Blue+'xml ='+str(x)
								print 'url ='+u+Cyan
						print ' ** Pause for '+str(p)+' seconds and try again'+White
						time.sleep(p)
				else:
						r=False
		return

subs = [
	['\t|\n', ' '],
	[u'\uFFFD', '?'],
	[u'Ì', 'I'],
	[u'ï', 'i'],
	[u'¸', ''],
	[u'¡', 'i'],
	[u'\x8c', '?'],
	[u"", 'Œ'],
	[u"Ã", u'Ü'], [u"Ã¤", u'ä'],
	[u'Ã¼', u'ü'], [u"u", u'ü'],
	[u'eÌ', u'é'],
	['&lt;|&gt;|\|\\\\', '-'],
	['\x5c|\|', '-'],
	[r'[:\/\<\>]+','-'],
	['&quot;|&#39;', "'"],
	['#|--','-'],
	["'{2,}", "'"], # titleblacklist-custom-double-apostrophe
	[' {2,}', ' '],
	['[\[\{]','('],
	['[\]\}]', ')'],
	['&amp;', '&'],
	['& ?c[\.;,]', 'etc.'],
	['\uFFFD', '~'],
	]

def dosubs(x, arr=subs):
	if re.search('&\w{1,5};', x):
		x = re.sub('(&\w{1,5});', r'\1' + ',', x)
	try:
		for s in arr:
			#print s
			x = re.sub(s[0], s[1], x)
	except Exception as e:
		print x
		print s
		print str(e)
		sys.exit()
	return x

wikisafe = [
	['\|', ';'],
	['[/:]', '-'],
	['\[', '('],
	['\]', ')'],
	]

def dsw(x):
	return dosubs(x, arr=wikisafe)

siArr = [
	['/ukmo/', 'UK Ministerial Orders', 'UKMO'],
	['/uksi/', 'United Kingdom Statutory Instruments', 'UKSI'],
	['/ukpga/','United Kingdom Public General Acts', 'UKPGA'],
	['/ukcm/', 'United Kingdom Church Measures', 'UKCM'],
	['/ukci/', 'United Kingdom Church Instruments', 'UKCI'],
	['/uksro/','UK Statutory Rules and Orders', 'UKSRO'],
	['/ukla/', 'UK Local Acts', 'UKLA'],
	['/ssi/',  'Scottish Statutory Instruments', 'SSI'],
	['/sdsi/', 'Scottish Statutory Instruments', 'SSI'],
	['/asp/',  'Scottish Acts', 'ASP'],
	['/aosp/', 'Acts of the Old Scottish Parliament', 'AOSP'],
	['/wsi/',  'Welsh Statutory Instruments', 'WSI'],
	['/mwa/',  'Measures of the National Assembly for Wales', 'MWA'],
	['/anaw/', 'Welsh National Assembly Acts', 'ANAW'],
	['/asc/',  'Welsh Parliament Acts', 'ASC'],
	['/eur/',  'European Union Regulations', 'EUR'],
	['/eudn/', 'European Union Decisions', 'EUD'],
	['/eudr/', 'European Union Directives', 'EUDR'],
	['/nisi/', 'Northern Ireland Orders in Council', 'NISI'],
	['/nisr/', 'Northern Ireland Statutory Rules', 'NISR'],
	['/nia/',  'Northern Ireland Acts', 'NIA'],
	['/nisro/','Northern Ireland Statutory Rules and Orders', 'NISRO'],
	['/aip/',  'Acts of the Old Irish Parliament', 'AIP'],
	['/apni/', 'Acts of the Northern Ireland Parliament', 'APNI'],
	['/apgb/', 'Acts of the Parliament of Great Britain', 'APGB'],
	['/aep/',  'Acts of the English Parliament', 'AEP'],
	]

def sicat(l):
	for a in siArr:
		if re.search(a[0], l):
			return a[1], a[2] + " " + re.sub('/', '-', l.split(a[0])[-1])
	return ""

skip=0
startyear = YEAR
endyear = startyear

if len(argv)>1:
	skip=int(float(argv[1]))
	if len(argv)>2:
		startyear = int(float(argv[2]))
		endyear = startyear
		if len(argv)>3:
			endyear = int(float(argv[3]))

base = "https://www.legislation.gov.uk/"

def mainloop(year):
	url = base + str(year) + "/data.feed?sort=published"
	html = htmltry(urltry(url), url)
	soup = BeautifulSoup(html, 'html.parser')
	facetyears = soup.find_all('leg:facetyear')
	yum = [f for f in facetyears if f['year'] == str(year)]
	if len(yum)!=1:
		#print yum
		#print Fore.CYAN, year, "gives 0 results", Fore.WHITE
		relex = False
		return
	yum = yum[0]
	ptotal = int(float(yum['total']))
	#print Fore.GREEN + "*"*70, Fore.WHITE
	#print Fore.YELLOW + "Total entries in {} are {}".format(year, ptotal)
	url = yum['href']
	#print "Feed url", url, Fore.WHITE
	#print Fore.GREEN + "*"*70, Fore.WHITE
	#url = base + str(year) + "/data.feed?sort=published"
	page = 1
	count = 0
	if skip > 20:
		page = int(skip/20.)
		count = page * 20
		url = url + "&page=" + str(page)
	while True:
		html = htmltry(urltry(url), url)
		soup = BeautifulSoup(html, 'html.parser')
		entries = [i for i in soup.find_all('entry')]
		#print Fore.CYAN, len(entries), entries[0].find('id').text.split('gov.uk/')[1]
		#print entries[0]
		nothingnew = True
		for entry in entries:
			count += 1
			if count<skip:
				continue
			title = entry.find('title').text.strip()
			shorttitle = title.split(' / ')[0]
			source = entry.find('link', {'rel':'self'})['href']
			#print source
			try:
				maincat, ckey = sicat(source)
			except:
				print Fore.MAGENTA, "Error parsing hierarchy from source name"
				print " source", source
				sys.exit()
			filename = dsw(shorttitle) + " (" + ckey + ").pdf"
			#print Fore.CYAN, "{}/{}".format(count, ptotal), Fore.GREEN + filename, Fore.WHITE
			try:
				pdf = ''
				pdfs = [e['href'] for e in entry.find_all('link', {'title':'PDF'})]
				pdfsx = [e['href'] for e in entry.find_all('link', {'title':"Print Version"}) if e['href'][-3:]=='pdf']
				if pdfsx != []:
					pdfs += pdfsx
				if pdfs!=[]:
					pdf = pdfs[0]
				if len(pdfs)>1:
					#print Fore.MAGENTA, "\n ".join(pdfs)
					#print " Multiple PDFs"
					#print " Page {}, count {}, ckey {}".format(page, count, ckey)
					#print "", source, Fore.WHITE
					pass
				if pdf[-3:] != "pdf":
					if re.search('Correction', filename):
						print Fore.MAGENTA, "Skipping correction slip", Fore.WHITE
						continue
					print Fore.MAGENTA, "No PDF?"
					print " Given file href of", pdf
					continue
			except Exception as e:
				#print Fore.MAGENTA, str(e), Fore.WHITE
				#print Fore.MAGENTA, "No PDF link found", Fore.WHITE
				continue
			try:
				published = entry.find('published').text
			except AttributeError:
				published = entry.find('ukm:year')['value']
			summary = entry.find('summary').text.strip()
			if summary=="":
				summary = title
			subjects = [s['value'] for s in entry.find_all('ukm:subject')]
			categories = [s['term'] for s in entry.find_all('category')]
			isbn = entry.find('ukm:isbn')
			if isbn != None:
				isbn = isbn.get('value')
			else:
				isbn = ''
			#xml = entry.find('link', {'title':'XML'})['href']
			dd = "== {{int:filedesc}} ==\n{{book"
			dd += "\n|description = {{en|1=" + dsw(summary) +"}}"
			dd += "\n|title = " + dsw(title)
			dd += "\n|source = " + source
			dd += "\n|date = " + published.split('T')[0]
			dd += "\n|other_fields = "
			if subjects != []:
				dd += "\n {{information field|name = Subjects|value = " + "; ".join(subjects) + "}}"
			if categories != subjects:
				dd += "\n {{information field|name = Categories|value = " + "; ".join(categories) + "}}"
			if isbn!='':
				dd += "\n|isbn = " + isbn		
			dd += "\n|noimage = 1\n}}"
			dd+="\n\n=={{int:license-header}}==\n"
			dd+="{{OGL3}}\n"
			dd+="\n{{DEFAULTSORT:" + ckey + "}}"
			dd+= "\n[[Category:" + maincat + "|" + ckey + "]]"
			dd+="\n[[Category:Images uploaded by {{subst:User:Fae/Fae}}]]"
			if pdf is None:
				#print Fore.MAGENTA, "No PDF found", Fore.WHITE
				continue
			if sicat(source) == "":
				print Fore.MAGENTA, "No sicat match for ", source, Fore.WHITE
				sys.exit()
			#print dd
			comment = (u"[[Commons:UK legislation project#Slurping|UK legislation project (slurp)]] {} ([[Category:" + maincat + "|" + maincat + "]]) {} 	#{}").format(year, ckey, count)
			if len(filename.encode('utf-8'))>240:
				filename = ckey + '.pdf'
				#print Fore.GREEN, "->", filename, Fore.WHITE
			ipage = pywikibot.Page(site, 'File:' + filename)
			try:
				if len(pdfs)==1 and ipage.exists():
					#print Fore.MAGENTA, "Exists", Fore.WHITE
					continue
			except Exception as e:
				if re.search('over 255 bytes', str(e)):
					filename = ckey + '.pdf'
					ipage = pywikibot.Page(site, 'File:' + filename)
					if ipage.exists():
						#print Fore.MAGENTA, "Exists", Fore.WHITE
						continue
				else:
					print Fore.MAGENTA, str(e), Fore.WHITE
					continue
			try:
				local = os.path.join(DIR , "UK legislation {}.pdf".format(year))
			except Exception as e:
				#print Fore.MAGENTA, str(e), Fore.WHITE
				sleep(60)
				continue
			for sourcep in pdfs:
				dloop = 1
				while dloop>0:
					try:
						urllib.urlretrieve(sourcep, local)
						dloop = 0
					except Exception as e:
						dloop += 1
						if dloop <5:
							print Fore.CYAN, dloop, "Error on urlretrieve", Fore.MAGENTA, str(e), Fore.WHITE
						sleep(10)
				fn = filename; clang = ''
				if len(pdfs)>1:
					if re.search("_we.pdf", sourcep):
						fn = re.sub("\).pdf$", " we).pdf", filename)
						clang = " (we)"
					if re.search("_en.pdf", sourcep):
						fn = re.sub("\).pdf$", " en).pdf", filename)
						clang = " (en)"
				ipage = pywikibot.Page(site, 'File:' + fn)
				try:
					if ipage.exists():
						#print Fore.MAGENTA, "Exists", Fore.WHITE
						continue
				except Exception as e:
					if re.search('over 255 bytes', str(e)):
						fn = ckey + '.pdf'
						ipage = pywikibot.Page(site, 'File:' + filename)
						if ipage.exists():
							#print Fore.MAGENTA, "Exists", Fore.WHITE
							continue
					else:
						print Fore.MAGENTA, str(e), Fore.WHITE
						continue
				nothingnew = False
				rec = uptry(local, fn, dd, comment + clang, False)
				if rec in ['verification-error', 'chunk-too-small']:
					#print Fore.MAGENTA, "Retrying download after", rec, "flagged", Fore.WHITE
					os.remove(local)
					urllib.urlretrieve(sourcep, local)
					sleep(4)
					rec = uptry(local, fn, dd, comment+clang, False)
					sleep(4)
					if rec in ['verification-error']:
						#print Fore.MAGENTA, "Retrying download after", rec, "flagged", Fore.WHITE
						os.remove(local)
						sleep(10)
						urllib.urlretrieve(sourcep, local)
						sleep(15)
						rec = uptry(local, fn, dd, comment+clang, False)
				os.remove(local)
		if nothingnew: # There were no upload attempts from the page given
			return
		next = soup.find('link', {'rel':'next'})
		if next is None:
			#print Fore.YELLOW, url
			#print Fore.CYAN, "Page", page, "Forecast", int(1+ptotal/20.)
			#print Fore.CYAN, "No next page in data.feed found", Fore.WHITE
			return False
		else:
			next = next['href']
			page = next.split('page=')[1]
			url = next
			#print Fore.YELLOW, "--", url, "--", Fore.WHITE

years = range(startyear, endyear + 1)
for year in years:
	relex = True
	while relex:
		relex = mainloop(year)
	skip = 0
