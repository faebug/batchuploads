#!/usr/bin/python
# -*- coding: utf-8 -*-
NOTICE = '''
Upload any missing Xeno-Canto audio files, but only if cc-by licensed

Not a url upload white-listed site, so local download needed

Date:
	2013 July Creation
	2018 April rewrite, initially with Juypiter lab
    	Dropped file conversion now mp3 is allowed
    	Add cc-by-4.0 option

Example command line:
python2 pwb.py batch_xenocanto

Author:			Fae, http://j.mp/faewm
Permissions:	CC-BY-SA-4.0
'''

import pywikibot
import urllib, urllib2, json, re, time, sys
from os import remove
from pywikibot import pagegenerators
from BeautifulSoup import BeautifulSoup
from colorama import Fore, Back, Style, init; init()

site = pywikibot.Site('commons','commons')

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
		site.upload(pywikibot.ImagePage(site, 'File:' + pagetitle),
			source_filename=source_filename, 
			source_url=source_url,
			comment=comment, 
			text=desc,
			ignore_warnings = True,
			chunk_size=1048576
			)
	else:
		site.upload(pywikibot.ImagePage(site, 'File:' + pagetitle),
			source_filename=source_filename, 
			source_url=source_url,
			comment=comment, 
			text=desc,
			chunk_size = 1048576
			)

def urltry(u):
    headers = { 'User-Agent' : 'Mozilla/5.0' } # Spoof header
    countErr=0; x=''
    while x=='':
        try:
            req = urllib2.Request(u,None,headers)
            x = urllib2.urlopen(req)
            time.sleep(1)
        except Exception as e:
            countErr+=1
            print Fore.RED, countErr, str(e), Fore.WHITE
            if countErr>3: return ' '
            print Fore.CYAN, '** ERROR',countErr,'\n ** Failed to read from '+ Fore.YELLOW +u+ Fore.CYAN +'\n ** Pause for '+str(countErr*10)+' seconds and try again ['+time.strftime("%H:%M:%S")+']', Fore.WHITE
            time.sleep(10*countErr)
    return x

def htmltry(x,u):
		countErr=0
		r=True
		while r:
				try:
						return x.read()
				except Exception as e:
						x=urltry(u)
						countErr+=1
						print Fore.RED, countErr, str(e), Fore.WHITE
						if countErr>200:
								p=300
						else:
								p=countErr*2
						print Fore.CYAN,'** ERROR',countErr,'\n ** Failed to read xml'
						if countErr==1:
								print Fore.BLUE +'xml ='+str(x)
								print 'url ='+u+ Fore.CYAN
						print ' ** Pause for '+str(p)+' seconds and try again'+ Fore.WHITE
						time.sleep(p)
				else:
						r=False
		return

SEARCHMAX = 10
def search(v):
		vcount=0
		countErr=0
		loop=True
		plist = set()
		while loop:
				try:
					vgen = pagegenerators.SearchPageGenerator(v, namespaces = "6")
					for vPage in vgen:
						plist.add(vPage.title())
						vcount+=1
						if vcount>= SEARCHMAX :
							loop = False
							break
					loop=False
				except Exception as e:
					print Fore.RED, str(e), Fore.WHITE
					loop=True
					countErr+=1
					print Fore.RED +"Problem running search, sleeping for",countErr,"seconds",Fore.WHITE
					time.sleep(countErr)
				if countErr>30:
					loop=False
					vcount=-1
		return plist

print Fore.GREEN + NOTICE, Fore.WHITE

DIR = "/Volumes/2GB/"
count = 0; skip = 0
baseurl = "http://www.xeno-canto.org/api/recordings.php?query=lic:by-sa&page="
page = 1
url = baseurl + str(page)
uri = urltry(url)
data = json.load(uri)
numPages = data['numPages']
for page in range(1,numPages + 1):
	url = baseurl + str(page)
	uri = urltry(url)
	data = json.load(uri)
	recordings=data['recordings']
	for r in recordings:
		count += 1
		if count < skip: continue
		ref=re.sub("\D*","",r['id'])
		species=r['sp']
		genus=r['gen']
		common=r['en']
		title=genus+" "+species+" - "+common+" XC"+ref
		filename=title + ".mp3"
		if count % 100 == 0:
			print Fore.GREEN + "{:0>5}".format(count), "-"*40, Fore.YELLOW + time.strftime("%H:%M:%S"), Fore.WHITE
		if pywikibot.FilePage(site, 'File:' + filename).exists()\
		or pywikibot.FilePage(site, 'File:' + title + ".ogg").exists():
			continue
		matches = search("intitle:XC" + ref + " filetype:AUDIO")
		if len(matches)>1:
			print Fore.RED, "Xenocanto ID in use"
			print Fore.CYAN + '   ' + '\n   '.join(m[5:] for m in matches), Fore.WHITE
			continue
		print Fore.CYAN + "{:0>5}".format(count), Fore.GREEN + filename
		source=r['file']
		if re.match(u"//", source): source = 'https:' + source
		artist=r['rec']
		gallery=r['url']
		url=urltry(gallery)
		html=htmltry(url,gallery)
		soup=BeautifulSoup(html)
		lic = soup.findAll('a', href=re.compile('.*?creativecommons.org'))[-1]['href']
		if re.search("by-sa/4", lic):
			license = "{{Cc-by-sa-4.0}}"
		elif re.search("by-sa/3", lic):
			license = "{{Cc-by-sa-3.0}}"
		else:
			print Fore.RED, lic
			print " Unexpected license?", Fore.WHITE
		rd=str(soup.find('section',{'id':'recording-data'}).find('tbody'))
		date=rd.split(">Date<")[1].split('<td>')[1].split('<')[0]
		dtime=""
		if re.search(">Time<",rd):
				dtime=rd.split(">Time<")[1].split('<td>')[1].split('<')[0]
				if len(dtime)>2:
						date+=" "+dtime
		elevation=''
		if re.search('>Elevation<',rd):
				elevation=rd.split(">Elevation<")[1].split('<td>')[1].split('<')[0]
		background=''
		if re.search('>Background<',rd):
				background=rd.split(">Background")[1].split('<td')[1].split('>')[1].split('<')[0]
				if background=="none":
						background=''
		remarks=''
		if re.search('<h2>Remarks from',html):
				remarks=html.split('<h2>Remarks')[1].split('h2>')[1]
				if re.search('<.section',remarks):
						remarks=remarks.split('</section')[0]
				remarks=re.sub("<.?p>","\n",remarks)
				remarks=re.sub("<.?span[^>]*?>","\n",remarks)
				remarks=re.sub("\n*\s*<$","",remarks)
				remarks=re.sub("\n+","\n:",re.sub("\s*\n\s*","\n",remarks))
				remarks=re.sub("<a [^>]*>","",re.sub("<\/a>","",remarks))
		d=u"=={{int:filedesc}}==\n{{information"
		d+="\n|description={{en|1="
		if remarks!='':
			d+=remarks.decode('utf-8')
		if len(r['en'])>2:
				d+="\n:'''Common name:''' "+r['en']
		if len(r['type'])>2:
				d+="\n:'''Type:''' "+r['type']
		if len(r['gen'])>2:
				d+="\n:'''Genus:''' "+r['gen']
		if len(r['sp'])>2:
				d+="\n:'''Species:''' "+r['sp']
		if len(r['loc'])>2:
				d+="\n:'''Location:''' "+r['loc']
		if len(r['cnt'])>2:
				d+="\n:'''Country:''' "+r['cnt']
		if elevation!='':
				d+="\n:'''Elevation:''' "+elevation
		if background!='':
				d+="\n:Background:''' "+background
		d+="}}"
		d+="\n|date="+date
		d+="\n|author="+artist
		d+="\n|source=\n:Metadata: "+gallery+"\n:Audio file: "+source
		d+="\n}}"
		if r['lat'] is not None and len(r['lat'])>2:
				d+="\n{{object location dec|"+r['lat']+"|"+r['lng']+"}}"
		d+="{{User:{{subst:User:Fae/Fae}}/Projects/Xeno-canto/credit}}"
		d+="\n\n=={{int:license-header}}==\n" + license + "\n"
		cat=r['gen']+" "+r['sp']
		if pywikibot.Page(site, 'Category:' + cat).exists():
				d+="\n[[Category:"+cat+"]]"
		d+="\n[[Category:Xeno-canto]]\n[[Category:Sound files uploaded by {{subst:User:Fae/Fae}}]]"
		print Fore.CYAN+d,Fore.WHITE
		localfile = DIR + ref + '.mp3'
		urllib.urlretrieve(source, localfile)
		comment = "Xenocanto batch #{}, {}".format(count, gallery)
		try:
			up(localfile, filename, d, comment, False)
		except Exception as e:
			if re.search("verification-error", str(e)):
				print Fore.MAGENTA, "Error probably due to restricted species at source", Fore.WHITE
			else:
				print Fore.RED, "Error at upload"
				print Fore.RED, str(e),Fore.WHITE
				sleep(300)
		remove(localfile)
